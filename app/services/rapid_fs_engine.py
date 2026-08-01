from typing import Dict, Any, Tuple, List
from app.schemas.rapid_fs import RapidFSInput, RapidFSResult, ComponentScores, CostBreakdown

# Default Ecosystem Parameters
ECOSYSTEM_DEFAULTS = {
    "hutan_tropis": {"cf": 150.0, "er": 5.0, "biodiversity": 85.0, "legality": 90.0},
    "mangrove": {"cf": 200.0, "er": 10.0, "biodiversity": 90.0, "legality": 85.0},
    "agroforestri": {"cf": 100.0, "er": 4.0, "biodiversity": 70.0, "legality": 80.0},
    "gambut": {"cf": 180.0, "er": 8.0, "biodiversity": 80.0, "legality": 75.0},
    "lahan_terdegradasi": {"cf": 60.0, "er": 3.0, "biodiversity": 50.0, "legality": 95.0},
}

def calculate_rapid_fs(input_data: RapidFSInput, spatial_override: Dict[str, Any] = None) -> RapidFSResult:
    """
    Mengimplementasikan 7-Stage Rapid-FS Scoring Engine sesuai spesifikasi dokumen Profil Satubumi.
    """
    area = input_data.area_ha
    years = input_data.project_duration_years
    cp = input_data.carbon_price_usd
    eco_type = input_data.ecosystem_type.lower()
    
    # Ambil parameter acuan ekosistem
    eco_config = ECOSYSTEM_DEFAULTS.get(eco_type, ECOSYSTEM_DEFAULTS["hutan_tropis"])
    cf = eco_config["cf"]
    er = eco_config["er"]
    spatial_layers = None
    
    # Override jika ada statistik riil dari ekstraksi GEE
    if spatial_override:
        if "cf" in spatial_override: cf = spatial_override["cf"]
        if "er" in spatial_override: er = spatial_override["er"]
        if "spatial_overlay_layers" in spatial_override: spatial_layers = spatial_override["spatial_overlay_layers"]
    
    # Tahap 3: Estimasi Karbon
    agb = area * cf                      # Above-Ground Biomass (ton)
    carbon_stock = agb * 0.47            # Carbon Stock (tC)
    co2e = carbon_stock * 3.67           # CO2 Equivalent (tCO2e)
    
    # Tahap 4: Estimasi Potensi Kredit Karbon (ACC)
    annual_er = er * area                # tCO2e / tahun
    acc_total = annual_er * years        # Total Kredit Karbon (tCO2e)
    
    # Tahap 5: Estimasi Pendapatan (Gross Revenue)
    gross_revenue = acc_total * cp       # USD
    
    # Tahap 6: Estimasi Biaya (Total Cost)
    dev_cost = 150000.0
    mrv_cost = 75000.0
    val_cost = 50000.0
    ops_cost = 100000.0
    fixed_cost = dev_cost + mrv_cost + val_cost + ops_cost  # USD 375,000
    
    variable_cost_per_ha = 5.0
    variable_cost_total = variable_cost_per_ha * area * years
    total_cost = fixed_cost + variable_cost_total
    
    net_revenue = gross_revenue - total_cost
    
    # Tahap 7: Skor Kelayakan & Pembobotan (FS)
    # C: Skor Karbon (0-100) berdasarkan intensitas penyerapan karbon
    c_score = min(100.0, max(10.0, (er / 10.0) * 100.0))
    
    # L: Skor Legalitas
    l_score = eco_config["legality"]
    
    # B: Skor Biodiversitas
    b_score = eco_config["biodiversity"]
    
    # S: Skor Sosial
    s_score = 75.0
    
    # E: Skor Ekonomi (berdasarkan margin keuntungan / ROI)
    if total_cost > 0:
        profit_margin = net_revenue / max(1.0, gross_revenue)
        e_score = min(100.0, max(0.0, profit_margin * 100.0))
    else:
        e_score = 50.0
        
    # Formula Pembobotan FS
    # FS = (C * 0.35) + (L * 0.20) + (B * 0.15) + (S * 0.10) + (E * 0.20)
    fs_score = (c_score * 0.35) + (l_score * 0.20) + (b_score * 0.15) + (s_score * 0.10) + (e_score * 0.20)
    fs_score = round(fs_score, 2)
    
    # Kategori Kelayakan
    if fs_score >= 81.0:
        category = "Potensi Tinggi"
    elif fs_score >= 61.0:
        category = "Potensi Sedang"
    elif fs_score >= 41.0:
        category = "Potensi Rendah"
    else:
        category = "Tidak Layak"
        
    # Rekomendasi Taksonomi
    recommendations = generate_recommendations(category, eco_type, area, net_revenue)
    
    comp_scores = ComponentScores(
        carbon_score=round(c_score, 1),
        legality_score=round(l_score, 1),
        biodiversity_score=round(b_score, 1),
        social_score=round(s_score, 1),
        economy_score=round(e_score, 1)
    )
    
    cost_bd = CostBreakdown(
        development_cost_usd=dev_cost,
        mrv_cost_usd=mrv_cost,
        validation_cost_usd=val_cost,
        operational_cost_usd=ops_cost,
        total_cost_usd=round(total_cost, 2)
    )
    
    return RapidFSResult(
        location_name=input_data.location_name or "Lokasi Proyek",
        area_ha=area,
        ecosystem_type=eco_type,
        project_duration_years=years,
        carbon_price_usd=cp,
        carbon_factor=cf,
        emission_reduction_rate=er,
        agb_ton=round(agb, 2),
        carbon_stock_tc=round(carbon_stock, 2),
        co2e_ton=round(co2e, 2),
        annual_emission_reduction=round(annual_er, 2),
        acc_total_credits=round(acc_total, 2),
        gross_revenue_usd=round(gross_revenue, 2),
        cost_breakdown=cost_bd,
        net_revenue_usd=round(net_revenue, 2),
        feasibility_score=fs_score,
        feasibility_category=category,
        component_scores=comp_scores,
        recommendations=recommendations,
        spatial_overlay_layers=spatial_layers,
        geometry=input_data.polygon_geojson
    )

def generate_recommendations(category: str, eco_type: str, area: float, net_revenue: float) -> List[str]:
    recs = []
    if category == "Potensi Tinggi":
        recs.append("Wilayah memiliki kelayakan tinggi untuk segera melanjutkan ke tahap Feasibility Study rinci (Full FS).")
        recs.append("Lakukan pengumpulan baseline data lapangan untuk inventarisasi flora/fauna dan konfirmasi status legalitas hutan.")
    elif category == "Potensi Sedang":
        recs.append("Proyek potensial namun memerlukan optimalisasi luas area atau integrasi skema agroforestri/restorasi.")
        recs.append("Lakukan penilaian ulang variabel biaya operasional dan negosiasi harga kredit karbon minimal USD 12-15/tCO2e.")
    else:
        recs.append("Skor kelayakan relatif rendah pada skala luas area saat ini.")
        recs.append("Disarankan melakukan konsolidasi wilayah dengan menambahkan area di sekitarnya untuk menutupi fixed cost pengembangan.")
        
    if area < 5000:
        recs.append("Catatan: Skala area < 5.000 ha memiliki rasio fixed cost tinggi per hektare.")
    return recs
