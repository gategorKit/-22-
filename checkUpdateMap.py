import math

R = 6371000

# Функция для расчета расстояния между двумя точками на Земле
def haversine(lat1, lon1, lat2, lon2):
    if lat1 !=None:
        lat1_rad = math.radians(lat1)
    else: lat1_rad = 0
    if lon1 !=None:
        lon1_rad = math.radians(lon1)
    else: lon1_rad = 0
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    delta_lat = lat2_rad - lat1_rad
    delta_lon = lon2_rad - lon1_rad
    
    a = math.sin(delta_lat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    metres = R * c
    return (metres>100)
