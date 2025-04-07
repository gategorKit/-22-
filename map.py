import requests
import time
import hashlib
import os


def get_osm_map(lat, lon, zoom, width=200, height=200):
    API_KEY = "10a81f2f277e4320acdb02993ece6702"

    # Уникальное имя файла на основе координат и зума
    unique_key = hashlib.md5(f"{lat}_{lon}_{zoom}".encode()).hexdigest()[:8]
    filename = f"map_{zoom}_{unique_key}.png"

    if os.path.exists(filename):
        print(f"Используем кэшированную карту: {filename}")
        return filename

    # Исправленный URL с правильным параметром center
    url = f"https://maps.geoapify.com/v1/staticmap?style=osm-bright&width={width}&height={height}" \
          f"&center=lonlat:{lon},{lat}&zoom={zoom}&apiKey={API_KEY}" \
          f"&marker=lonlat:{lon},{lat};type:material;color:red;size:large"

    print(f"Запрос карты для координат: {lat}, {lon}, zoom: {zoom}")
    start_time = time.time()

    try:
        response = requests.get(url, stream=True, timeout=10)
        response.raise_for_status()  # Проверка на ошибки HTTP
    except requests.RequestException as e:
        print(f"Ошибка загрузки карты: {e}")
        return None  # Возвращаем None, если запрос не удался

    with open(filename, "wb") as file:
        for chunk in response.iter_content(1024):
            file.write(chunk)
    end_time = time.time()
    print(f"Карта {filename} сохранена за {end_time - start_time:.2f} секунд")
    return filename
