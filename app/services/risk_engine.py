from datetime import datetime, date, time, timezone

def calculate_risk(rain_prob: float, wind_speed: float, temp: float):
    # Rain Risk
    if rain_prob >= 0.7:
        rain_risk = "HIGH"
    elif rain_prob >= 0.3:
        rain_risk = "MEDIUM"
    else:
        rain_risk = "LOW"
        
    # Wind Risk
    if wind_speed >= 15:
        wind_risk = "HIGH"
    elif wind_speed >= 8:
        wind_risk = "MEDIUM"
    else:
        wind_risk = "LOW"
        
    # Heat Risk
    if temp >= 35:
        heat_risk = "HIGH"
    elif temp >= 30:
        heat_risk = "MEDIUM"
    else:
        heat_risk = "LOW"
        
    # Overall Risk
    risks = [rain_risk, wind_risk, heat_risk]
    if "HIGH" in risks:
        overall_risk = "HIGH"
    elif "MEDIUM" in risks:
        overall_risk = "MEDIUM"
    else:
        overall_risk = "LOW"
        
    return rain_risk, wind_risk, heat_risk, overall_risk

def process_worst_case_scenario(weather_data: dict, event_date: date, event_start: time, event_end: time):
    if not weather_data or "list" not in weather_data:
        return None
        
    # Konversi event start dan end ke datetime UTC untuk perbandingan
    # Asumsi: Untuk penyederhanaan saat memproses timestamp UTC dari OWM,
    # kita bandingkan dengan jam acara. Dalam skenario nyata yang kompleks, 
    # perhitungan timezone spesifik lokasi perlu diperhatikan matang.
    
    worst_temp = -100
    worst_wind = -1
    worst_rain = -1
    worst_hum = -1
    worst_cloud = -1
    worst_time = None
    
    found_overlap = False
    
    from datetime import timedelta
    
    # Buat datetime untuk event_start dan event_end
    event_start_dt = datetime.combine(event_date, event_start, tzinfo=timezone.utc)
    event_end_dt = datetime.combine(event_date, event_end, tzinfo=timezone.utc)
    if event_end < event_start:
        event_end_dt += timedelta(days=1)
        
    for item in weather_data["list"]:
        dt = datetime.fromtimestamp(item["dt"], tz=timezone.utc)
        item_end_dt = dt + timedelta(hours=3)
        
        # Cek overlap: start1 < end2 and end1 > start2
        # Disini kita tidak lagi memaksa filter dt.date() == event_date saja,
        # melainkan menggunakan absolute datetime interval untuk overlap yang akurat.
        if dt < event_end_dt and item_end_dt > event_start_dt:
            found_overlap = True
            
            temp = item["main"]["temp"]
            wind = item["wind"]["speed"]
            rain = item.get("pop", 0.0) # Probability of precipitation
            hum = item["main"].get("humidity", 0.0)
            cloud = item.get("clouds", {}).get("all", 0.0)
            
            # Update worst cases
            if temp > worst_temp:
                worst_temp = temp
            if wind > worst_wind:
                worst_wind = wind
            if rain > worst_rain:
                worst_rain = rain
                worst_time = dt.time()
            if hum > worst_hum:
                worst_hum = hum
            if cloud > worst_cloud:
                worst_cloud = cloud

    if not found_overlap:
        return None
        
    return {
        "temperature": worst_temp if worst_temp != -100 else None,
        "wind_speed": worst_wind if worst_wind != -1 else None,
        "rain_probability": worst_rain if worst_rain != -1 else None,
        "humidity": worst_hum if worst_hum != -1 else 0.0,
        "cloud_coverage": worst_cloud if worst_cloud != -1 else 0.0,
        "worst_case_time": worst_time
    }
