import os
from io import BytesIO
from jinja2 import Template

PDF_HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Satubumi Carbon Feasibility Assessment Report</title>
    <style>
        body { font-family: 'Helvetica', 'Arial', sans-serif; color: #1e293b; margin: 0; padding: 25px; line-height: 1.5; }
        .header { text-align: center; border-bottom: 3px solid #059669; padding-bottom: 15px; margin-bottom: 25px; }
        .logo { font-size: 26px; font-weight: bold; color: #047857; letter-spacing: 1px; }
        .subtitle { font-size: 13px; color: #64748b; margin-top: 5px; }
        .badge { display: inline-block; padding: 8px 18px; border-radius: 20px; font-weight: bold; color: white; margin-top: 10px; font-size: 16px; }
        .badge-high { background-color: #059669; }
        .badge-medium { background-color: #d97706; }
        .badge-low { background-color: #dc2626; }
        
        .section { margin-bottom: 25px; }
        .section-title { font-size: 16px; font-weight: bold; color: #065f46; border-left: 4px solid #059669; padding-left: 10px; margin-bottom: 12px; }
        
        table { width: 100%; border-collapse: collapse; margin-top: 10px; font-size: 13px; }
        th, td { border: 1px solid #cbd5e1; padding: 10px 12px; text-align: left; }
        th { background-color: #f1f5f9; color: #334155; font-weight: bold; }
        .number { text-align: right; }
        
        .grid { display: flex; justify-content: space-between; margin-bottom: 15px; }
        .card { background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 15px; width: 45%; }
        .card-val { font-size: 22px; font-weight: bold; color: #047857; }
        
        .footer { margin-top: 40px; font-size: 11px; color: #94a3b8; text-align: center; border-top: 1px solid #e2e8f0; padding-top: 15px; }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">SATUBUMI.ORG</div>
        <div class="subtitle">Indicative Carbon Project Feasibility Assessment (Rapid-FS Report)</div>
        <div class="badge {% if score >= 81 %}badge-high{% elif score >= 61 %}badge-medium{% else %}badge-low{% endif %}">
            Skor Kelayakan: {{ score }} / 100 ({{ category }})
        </div>
    </div>

    <div class="section">
        <div class="section-title">1. Ringkasan Informasi Proyek</div>
        <table>
            <tr><th>Nama Lokasi</th><td>{{ location_name }}</td></tr>
            <tr><th>Luas Wilayah</th><td>{{ "{:,.2f}".format(area_ha) }} Hektare</td></tr>
            <tr><th>Tipe Ekosistem</th><td>{{ ecosystem_type | upper }}</td></tr>
            <tr><th>Durasi Proyek</th><td>{{ project_duration_years }} Tahun</td></tr>
            <tr><th>Asumsi Harga Karbon</th><td>USD {{ "{:,.2f}".format(carbon_price_usd) }} / tCO2e</td></tr>
        </table>
    </div>

    <div class="section">
        <div class="section-title">2. Estimasi Stok Karbon & Kredit Karbon (ACC)</div>
        <table>
            <thead>
                <tr>
                    <th>Indikator Metrik</th>
                    <th class="number">Nilai Estimasi</th>
                </tr>
            </thead>
            <tbody>
                <tr><td>Above-Ground Biomass (AGB)</td><td class="number">{{ "{:,.2f}".format(agb_ton) }} Ton</td></tr>
                <tr><td>Cadangan Karbon (Carbon Stock)</td><td class="number">{{ "{:,.2f}".format(carbon_stock_tc) }} tC</td></tr>
                <tr><td>Konversi CO₂ Ekuivalen (CO₂e)</td><td class="number">{{ "{:,.2f}".format(co2e_ton) }} tCO₂e</td></tr>
                <tr><td>Laju Penurunan Emisi Tahunan (ER)</td><td class="number">{{ "{:,.2f}".format(annual_er) }} tCO₂e / ha / thn</td></tr>
                <tr><th>Total Kredit Karbon (ACC 30 Thn)</th><th class="number">{{ "{:,.2f}".format(acc_total_credits) }} tCO₂e</th></tr>
            </tbody>
        </table>
    </div>

    <div class="section">
        <div class="section-title">3. Estimasi Proyeksi Keuangan</div>
        <table>
            <thead>
                <tr>
                    <th>Komponen Keuangan</th>
                    <th class="number">Proyeksi Nilai (USD)</th>
                </tr>
            </thead>
            <tbody>
                <tr><td>Estimasi Pendapatan Kotor (Gross Revenue)</td><td class="number">$ {{ "{:,.2f}".format(gross_revenue_usd) }}</td></tr>
                <tr><td>Estimasi Biaya Tetap (Fixed Costs)</td><td class="number">$ 375,000.00</td></tr>
                <tr><td>Estimasi Biaya Total (Total Cost)</td><td class="number">$ {{ "{:,.2f}".format(total_cost_usd) }}</td></tr>
                <tr><th>Estimasi Pendapatan Bersih (Net Revenue)</th><th class="number">$ {{ "{:,.2f}".format(net_revenue_usd) }}</th></tr>
            </tbody>
        </table>
    </div>

    <div class="section">
        <div class="section-title">4. Pembobotan Sub-Skor & Rekomendasi Takris</div>
        <ul>
            {% for rec in recommendations %}
                <li>{{ rec }}</li>
            {% endfor %}
        </ul>
    </div>

    <div class="footer">
        Laporan ini dihasilkan secara otomatis oleh Satubumi Rapid-FS Engine sebagai studi awal indikatif (Initial Screening).<br>
        © 2026 Satubumi.org — Climate & Sustainability Advisory Services.
    </body>
</html>
"""

def generate_pdf_report(assessment_data: dict) -> bytes:
    """
    Mengompilasi template HTML dengan Jinja2 dan merender file PDF.
    Menggunakan WeasyPrint jika tersedia, atau fallback HTML generator.
    """
    template = Template(PDF_HTML_TEMPLATE)
    html_content = template.render(
        location_name=assessment_data.get("location_name", "Lokasi Proyek"),
        area_ha=assessment_data.get("area_ha", 0),
        ecosystem_type=assessment_data.get("ecosystem_type", "hutan_tropis"),
        project_duration_years=assessment_data.get("project_duration_years", 30),
        carbon_price_usd=assessment_data.get("carbon_price_usd", 10.0),
        score=assessment_data.get("feasibility_score", 0),
        category=assessment_data.get("feasibility_category", "N/A"),
        agb_ton=assessment_data.get("agb_ton", 0),
        carbon_stock_tc=assessment_data.get("carbon_stock_tc", 0),
        co2e_ton=assessment_data.get("co2e_ton", 0),
        annual_er=assessment_data.get("annual_emission_reduction", 0),
        acc_total_credits=assessment_data.get("acc_total_credits", 0),
        gross_revenue_usd=assessment_data.get("gross_revenue_usd", 0),
        total_cost_usd=assessment_data.get("total_cost_usd", assessment_data.get("cost_breakdown", {}).get("total_cost_usd", 0)),
        net_revenue_usd=assessment_data.get("net_revenue_usd", 0),
        recommendations=assessment_data.get("recommendations", [])
    )
    
    try:
        from weasyprint import HTML
        pdf_bytes = HTML(string=html_content).write_pdf()
        return pdf_bytes
    except Exception as e:
        # Fallback render HTML string jika system library WeasyPrint belum di-install
        return html_content.encode('utf-8')
