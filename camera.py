import os
import sys
from random import randint
import cv2
import time
import serial
from PySide6.QtGui import QGuiApplication, QImage
from PySide6.QtQuick import QQuickImageProvider
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtCore import QObject, QThread, Signal, Slot, QRunnable, QThreadPool, QMutex
import requests
import glob
import takeData
import json
import map
import checkUpdateMap

os.environ['LIBGL_ALWAYS_SOFTWARE'] = '1'
os.environ['GST_GL_WINDOW'] = 'x11'

"""with open("/home/orangepi/Desktop/PythonProject1/config.json", "r", encoding="utf-8") as f:
    config = json.load(f)"""
    
with open("/home/user/Desktop/-22--camera/config.json", "r", encoding="utf-8") as f:
    config = json.load(f)


class CameraImageProvider(QQuickImageProvider):
    def __init__(self):
        super().__init__(QQuickImageProvider.Image)
        self._current_frame = QImage()
        self._lock = QMutex()

    def requestImage(self, name, size, requestedSize):
        self._lock.lock()
        img = self._current_frame.copy() if not self._current_frame.isNull() else QImage()
        self._lock.unlock()
        return img

    def update_frame(self, frame: QImage):
        if not frame.isNull():
            self._lock.lock()
            self._current_frame = frame.copy()
            self._lock.unlock()


class CameraWorker(QThread):
    frameChanged = Signal(QImage)

    def __init__(self, url):
        super().__init__()
        self.url = url
        self.running = True
        self.pipeline = (
			f"rtspsrc location={self.url} "
            "latency=10  protocols=tcp !"
            "queue ! "
            "rtph265depay ! "
            "h265parse ! "
            "mppvideodec ! "
            "videoconvert ! "
            "appsink"
        )

    def run(self):
        
        
        cap = cv2.VideoCapture(self.url, cv2.CAP_GSTREAMER)
        if not cap.isOpened():
            print("[CameraWorker] Ошибка: не удалось открыть поток")
            return

        while self.running:
            ret, frame = cap.read()
            
            if not ret:
                print("[CameraWorker] Ошибка чтения кадра. Переподключение...")
                time.sleep(1)
                continue

            rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            qt_image = QImage(rgb_image.data, frame.shape[1], frame.shape[0], frame.shape[1] * 3, QImage.Format.Format_RGB888)
            self.frameChanged.emit(qt_image)

        cap.release()

    def stop(self):
        self.running = False
        self.quit()
        self.wait()


class DataWorker(QThread):
    dataFetched = Signal(list)

    def __init__(self):
        super().__init__()
        
        self.running = True

    def run(self):
         # Отладка
        while self.running:
            try:
                data = takeData.get_data(config["gps_port"], config["arduino_port"])
                
                 # Отладка
                self.dataFetched.emit(data)
            except Exception as e:
                print(f"[DataWorker] Ошибка получения данных: {e}")  # Ловим ошибки
            #time.sleep(1)  # Интервал обновления

    def stop(self):
        print("[DataWorker] Остановка потока")  # Отладка
        self.running = False
        self.wait()


class MapTask(QRunnable):
    def __init__(self, x, y, zoom, callback):
        super().__init__()
        self.x = x
        self.y = y
        self.zoom = zoom
        self.callback = callback

    def run(self):
        img = map.get_osm_map(self.x, self.y, self.zoom)
        self.callback(self.zoom, img)


class MapWorker(QObject):
    mapUpdated = Signal(int, str)

    def __init__(self, latitude, longitude):
        super().__init__()
        self.running = True
        self.x1, self.y1 = latitude, longitude
        self.flag = False
        self.cache = {}
        self.thread_pool = QThreadPool.globalInstance()

    def getNewCoordinates(self, latitude, longitude):
        self.x2, self.y2 = latitude, longitude
        if ((self.x2 == 0) | (self.x2 is None)) & ((self.y2 == 0) | (self.y2 is None)):
            return False
        else:
            self.flag = checkUpdateMap.haversine(self.x1, self.y1, self.x2, self.y2)

        if self.flag:
            self.x1 = self.x2
            self.y1 = self.y2
            return True
        else:
            return False

    def createMap(self, zoom):
        self.clear_old_maps()
        for z in range(11, 16):
            cached_path = self.cache.get(z)
            if z not in self.cache or not isinstance(cached_path, str) or not os.path.exists(cached_path):
                task = MapTask(self.x1, self.y1, z, self.mapLoaded)
                self.thread_pool.start(task)
                print("create map")
            elif os.path.exists(cached_path):
                self.mapUpdated.emit(z, cached_path)
        return zoom

    def mapLoaded(self, zoom, img):
        if img and isinstance(img, str):
            self.cache[zoom] = img
            self.mapUpdated.emit(zoom, img)

    def clear_old_maps(self):
        for file in glob.glob("map_*.png"):
            try:
                os.remove(file)
                print(f"Удалён старый файл: {file}")
            except OSError as e:
                print(f"Ошибка удаления файла {file}: {e}")

    def stop(self):
        print("[MapWorker] Остановка")
        self.thread_pool.clear()


class Backend(QObject):
    updateTrigger = Signal()
    distTrigger = Signal()

    def __init__(self, img_provider):
        super().__init__()
        self.degree = 0
        self.pitch = 0.0
        self.roll = 0.0
        self.distance = 0
        self.enabled_zoom_map = False
        self.map_color = "white"
        self.image_provider = img_provider
        self.zoom = 15
        self.map = ""
        self.map_loading = True
        self.zoom_cam = 0
        self.zoom_map = 0
        self.show_distance = 0
        self.stop_zoom_flag = False
        

        # Инициализация свойств
        self.init_properties()

        
        self.data_worker = DataWorker()
        self.data_worker.dataFetched.connect(self.handle_data)
        self.data_worker.start()

        self.worker = CameraWorker(config["ip_camera"])
        self.worker.frameChanged.connect(self.update_frame)
        self.worker.start()

        self.map_worker = MapWorker(None, None)
        self.map_worker.mapUpdated.connect(self.handle_map_updated)
        self.map_worker.createMap(self.zoom)

    def init_properties(self):
        properties = {
            "map_img": "",
            "map_loading": self.map_loading,
            "enabled_zoom_map": self.enabled_zoom_map,
            "map_color": self.map_color,
            "distanceInMM": self.distance,
            "roll": self.roll,
            "pitch": self.pitch,
            "degree": self.degree
        }
        for key, value in properties.items():
            engine.rootContext().setContextProperty(key, value)
        self.clear_old_maps()

    def clear_old_maps(self):
        for file in glob.glob("map_*.png"):
            try:
                os.remove(file)
                print(f"Удалён старый файл: {file}")
            except OSError as e:
                print(f"Ошибка удаления файла {file}: {e}")

    @Slot(int, str)
    def handle_map_updated(self, zoom, img_path):
        if zoom == self.zoom and img_path:
            self.map = img_path
            self.map_loading = False
            self.enabled_zoom_map = True
            
           
            engine.rootContext().setContextProperty("map_img", self.map)
           

    def update_frame(self, frame: QImage):
        self.image_provider.update_frame(frame)
        """self.degree = randint(0,360)
        self.distance = randint(0,360)
        self.pitch = randint(0,360)
        self.roll = randint(0,360)
         
          
            

        context_updates = {
			 "distanceInMM": self.distance,
			 "roll": self.roll,
			 "pitch": self.pitch,
			 "degree": self.degree
         }
        for key, value in context_updates.items():
            engine.rootContext().setContextProperty(key, value)"""
        
        self.updateTrigger.emit()
        
    @Slot()
    def cam_zoom_in(self):
        url = "http://admin:admin@192.168.1.88/web/cgi-bin/hi3510/ptzctrl.cgi"
        params = {"-step": "0", "-act": "zoomin", "-speed": "45"}
        response = requests.get(url, params=params)
        self.stop_zoom_flag = True
        if response.status_code == 200:
            print("Zoom-in command sent successfully!")
        else:
            print(f"Failed to send zoom-in command. Status code: {response.status_code}")

    @Slot()
    def cam_zoom_out(self):
        url = "http://admin:admin@192.168.1.88/web/cgi-bin/hi3510/ptzctrl.cgi"
        params = {"-step": "0", "-act": "zoomout", "-speed": "45"}
        response = requests.get(url, params=params)
        self.stop_zoom_flag = True
        if response.status_code == 200:
            print("Zoom-out command sent successfully!")
        else:
            print(f"Failed to send zoom-out command. Status code: {response.status_code}")

    @Slot()
    def cam_zoom_stop(self):
        url = "http://admin:admin@192.168.1.88/web/cgi-bin/hi3510/ptzctrl.cgi"
        params = {"-step": "0", "-act": "stop", "-speed": "45"}
        if(self.stop_zoom_flag):
            response = requests.get(url, params=params)
            self.stop_zoom_flag = False
            """if response.status_code == 200:
				#print("Zoom-stop command sent successfully!")
			else:
				print(f"Failed to send zoom-stop command. Status code: {response.status_code}")"""
				

    @Slot()
    def zoom_in_map(self):
        if self.zoom < 15:
            self.zoom += 1
            self.map_loading = True
            engine.rootContext().setContextProperty("map_loading", self.map_loading)
            engine.rootContext().setContextProperty("map_img", "")
            self.map_worker.createMap(self.zoom)

    @Slot()
    def zoom_out_map(self):
        if self.zoom > 11:
            self.zoom -= 1
            self.map_loading = True
            engine.rootContext().setContextProperty("map_loading", self.map_loading)
            engine.rootContext().setContextProperty("map_img", "")
            self.map_worker.createMap(self.zoom)

    @Slot(list)
    def handle_data(self, data):
        try:
            """self.degree = round(float(data[0]))
            self.distance = float(data[2])
            self.pitch = float(data[3])
            self.roll = float(data[4])
            self.zoom_map = int(data[6])
            self.zoom_cam = int(data[7])
            self.show_distance = int(data[8])"""
            latitude, longitude = data[0], data[1]
            
            
                
            

            context_updates = {
                "distanceInMM": self.distance,
                "roll": self.roll,
                "pitch": self.pitch,
                "degree": self.degree
            }
            
            if self.zoom_map == 1:
                self.zoom_in_map()
            if self.zoom_map == -1:
                self.zoom_out_map()
            if self.zoom_cam == 1:
                self.cam_zoom_in()
            if self.zoom_cam == -1:
                self.cam_zoom_out()
            if self.zoom_cam == 0:
                self.cam_zoom_stop()
            if self.show_distance == 1:
                self.distTrigger.emit()
                
            for key, value in context_updates.items():
                engine.rootContext().setContextProperty(key, value)
            self.updateTrigger.emit()

            if self.map_worker.getNewCoordinates(latitude, longitude):
                self.map_loading = True
                self.enabled_zoom_map = False
           
                
                self.map_worker.cache.clear()
                self.map_worker.createMap(self.zoom)

            

        except (IndexError, ValueError) as e:
            print(f"[Backend] Ошибка обработки данных: {e}")

   

    def stop_worker(self):
        if self.worker.isRunning():
            self.worker.stop()
        if self.data_worker.isRunning():
            self.data_worker.stop()
        if self.map_worker:
            self.map_worker.stop()
        self.clear_old_maps()


if __name__ == "__main__":
    app = QGuiApplication(sys.argv)
    engine = QQmlApplicationEngine()

    camera_provider = CameraImageProvider()
    engine.addImageProvider("camera", camera_provider)

    backend = Backend(camera_provider)
    engine.rootContext().setContextProperty("backend", backend)

    try:
        engine.load("/home/user/Desktop/-22--camera/camera.qml")
        if not engine.rootObjects():
            sys.exit(-1)
        sys.exit(app.exec())
    except KeyboardInterrupt:
        backend.stop_worker()
