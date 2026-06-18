def generate_recommendation(rain_risk: str, wind_risk: str, heat_risk: str, overall_risk: str, worst_time=None) -> str:
    recommendations = []
    
    time_str = f" sekitar pukul {worst_time.strftime('%H:%M')}" if worst_time else ""

    if rain_risk == "HIGH":
        recommendations.append(f"Risiko hujan tinggi diperkirakan terjadi{time_str}. Sangat disarankan untuk memindahkan acara ke lokasi indoor atau menyediakan tenda tertutup berkapasitas penuh.")
    elif rain_risk == "MEDIUM":
        recommendations.append(f"Ada kemungkinan hujan ringan-sedang{time_str}. Sediakan jas hujan darurat atau area berteduh yang cukup.")
        
    if wind_risk == "HIGH":
        recommendations.append(f"Kecepatan angin sangat berbahaya{time_str}. Segera amankan seluruh struktur sementara (tenda, panggung, banner) agar tidak roboh atau terbang.")
    elif wind_risk == "MEDIUM":
        recommendations.append("Angin cukup kencang. Pastikan perlengkapan ringan dan dekorasi terpasang dengan kuat.")
        
    if heat_risk == "HIGH":
        recommendations.append(f"Suhu sangat ekstrem/panas{time_str}. Wajib sediakan area istirahat ber-AC, air minum ekstra, dan tim medis siaga untuk antisipasi heatstroke.")
    elif heat_risk == "MEDIUM":
        recommendations.append("Suhu cukup panas. Perbanyak titik air minum untuk peserta.")

    if overall_risk == "LOW":
        return "Kondisi cuaca diperkirakan sangat aman dan kondusif untuk pelaksanaan acara outdoor."
        
    if not recommendations:
        return "Lakukan persiapan standar untuk acara outdoor."
        
    return " ".join(recommendations)
