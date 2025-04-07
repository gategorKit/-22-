import serial
import serial.tools.list_ports
import time
import threading
import queue
import pynmea2
from pynmeagps import NMEAReader


def is_nmea_sentence(data):
    return (line.startswith('$') and (',' in line) and ('*' in line) for line in data)

def is_hex_string(data):
    return (c in '0123456789ABCDEFabcdef' for c in data)

def identify_ports():
    ports = [port.device for port in serial.tools.list_ports.comports()]
    gps_baud = 115200
    print(ports)
    
    arduino_baud = 74880
    gps_port = None
    arduino_port = None

    for port in ports:
        try:
            ser = serial.Serial(port, gps_baud, timeout=1)
            time.sleep(0.1)  # Ждем данных
            data = ser.readline().decode('utf-8', errors='ignore')
            print("port " + port)
            print("gps_data " + data)
            if is_nmea_sentence(data):
                gps_port = port
                break
        except serial.SerialException:
            pass
        finally:
            if ser:
                ser.close()

    for port in ports:
        
        try:
            ser = serial.Serial(port, arduino_baud, timeout=1)
            time.sleep(0.1)  # Ждем данных
            data = ser.readline().decode('utf-8', errors='ignore')
           
            
            
            if is_hex_string(data):
                arduino_port = port
                print("port " + arduino_port)
                break
        except serial.SerialException:
            pass
        finally:
            if ser:
                ser.close()

    return arduino_port

def parse_nmea(nmea_sentence):
    
    try:
        coord = NMEAReader.parse(nmea_sentence, validate=0)
        lat = coord.lat
        lon = coord.lon
        
    except Exception as e:
        print("Ошибка обработки NMEA: ", e)
        return None, None
    else:
        return lat, lon

def read_gps(gps_port, gps_queue):
    try:
        
        with serial.Serial(gps_port, 115200, timeout=0.1) as gps_data:
            
            gps_packet = gps_data.readline().decode('utf-8', errors='ignore').strip()
            
            			
            
            latitude, longitude = parse_nmea(gps_packet)
            print(latitude, "  ", longitude)
            if latitude is not None and longitude is not None:
                gps_queue.put((latitude, longitude))
        
    except serial.SerialException as e:
        print(f"Ошибка GPS: {e}")

def read_arduino(arduino_port, arduino_queue):
    try:
        with serial.Serial(arduino_port, 74880, timeout=1) as arduino_data:
            arduino_packet = arduino_data.readline().decode('utf-8', errors='ignore').strip()
            
           
            
            if all(c in '0123456789ABCDEFabcdef' for c in arduino_packet):
                try:
                    decoded_string = bytes.fromhex(arduino_packet).decode('utf-8')
                    
                    split_data = decoded_string.split(";")
                    
                    
                    
                    if split_data[0] != "15" or split_data[-1] != "255":
                        print("МАССИВ НЕПОЛНЫЙ")
                        return
                    split_data.pop(0)
                    split_data.pop(-1)
                    
                    arduino_queue.put(split_data)
                except ValueError:
                    print(f"Ошибка декодирования HEX: {arduino_packet}")
    except serial.SerialException as e:
        print(f"Ошибка Arduino: {e}")

def get_data(gps_port, arduino_port):
    
    gps_queue = queue.Queue()
    arduino_queue = queue.Queue()

    gps_thread = threading.Thread(target=read_gps, args=(gps_port, gps_queue))
    arduino_thread = threading.Thread(target=read_arduino, args=(arduino_port, arduino_queue))

    gps_thread.start()
    arduino_thread.start()

    gps_thread.join()
    arduino_thread.join()

    arduino_data = arduino_queue.get() if not arduino_queue.empty() else []
    gps_data = gps_queue.get() if not gps_queue.empty() else (None, None)

    
    arduino_data.append(gps_data[0])  # Добавляем широту
    arduino_data.append(gps_data[1])  # Добавляем долготу
    
    return arduino_data
    

ard = get_data("/dev/ttyS4", "/dev/ttyS0")


