# API Handoff — SATUBUMI MONITOR (Frontend Guide)

**Base URL:** `http://localhost:8000/api/v1`  
**Swagger Docs:** `http://localhost:8000/docs`  
**Auth:** Semua endpoint SATUBUMI MONITOR memerlukan header `Authorization: Bearer <access_token>`

> Modul ini ditambahkan di atas backend Rapid-FS yang sudah ada. Endpoint lama tidak berubah.

---

## 🗺️ Gambaran Besar

SATUBUMI MONITOR memiliki **2 lapisan endpoint**:

```
/api/v1/projects               → CRUD Proyek (master data)
/api/v1/projects/{id}/...      → Data Monitor per-Proyek
```

Semua data monitor (pohon, kegiatan, laporan, dll) **terikat ke satu `project_id`**.

---

## 📋 1. PROJECTS — Master Data Proyek

### `GET /projects`
Daftar semua proyek. *(Butuh login)*

**Response:**
```json
[
  {
    "id": 1,
    "name": "Proyek Restorasi Kalimantan Barat",
    "location_name": "Kalimantan Barat",
    "area_ha": 25430.0,
    "status": "active",
    "boundary_geojson": { "type": "Polygon", "coordinates": [...] },
    "targets_json": { "restoration_ha": 1000, "tree_planting": 100000 },
    "created_at": "2026-08-24T00:00:00",
    "updated_at": "2026-08-24T00:00:00"
  }
]
```

### `POST /projects` — Admin Only
```json
{
  "name": "Proyek Restorasi Kalimantan Barat",
  "location_name": "Kalimantan Barat",
  "area_ha": 25430.0,
  "status": "active",
  "boundary_geojson": {
    "type": "Polygon",
    "coordinates": [[[108.0, -1.0], [109.0, -1.0], [109.0, -2.0], [108.0, -2.0], [108.0, -1.0]]]
  },
  "targets_json": { "restoration_ha": 1000, "tree_planting": 100000 }
}
```
> `boundary_geojson` boleh `null`, bisa diisi nanti lewat `PUT`.

### `PUT /projects/{id}` — Admin Only
Semua field opsional, hanya yang dikirim yang berubah.

### `DELETE /projects/{id}` — Admin Only
Hapus proyek + **semua data monitor-nya ikut terhapus** (cascade).

---

## 📊 2. DASHBOARD

### `GET /projects/{id}/dashboard`
**Endpoint utama untuk halaman monitor.** Menggabungkan semua data.  
*(Juga auto-trigger cek `monitoring_overdue` setiap dipanggil)*

**Response:**
```json
{
  "project_id": 1,
  "project_name": "Proyek Restorasi Kalimantan Barat",
  "project_status": "active",
  "area_ha": 25430.0,
  "trees_planted": 125430,
  "trees_survived": 114643,
  "trees_dead": 10787,
  "survival_rate": 91.4,
  "carbon_stock_tco2e": 3200000.0,
  "estimated_co2e": 2900000.0,
  "species_recorded": 187,
  "total_beneficiaries": 2430,
  "total_villages": 12,
  "total_livelihood_groups": 27,
  "total_activities": 5,
  "recent_activities": [
    { "id": 1, "type": "planting", "date": "2026-08-22", "realization": 5000, "unit": "trees" }
  ],
  "active_alerts": 2,
  "recent_alerts": [
    { "id": 1, "type": "monitoring_overdue", "severity": "medium", "description": "...", "created_at": "..." }
  ],
  "total_field_reports": 34,
  "last_field_report": "2026-08-20T09:00:00"
}
```

---

## 🌱 3. PROJECT ACTIVITIES — Kegiatan Proyek

**Jenis kegiatan yang valid:**
`planting` | `restoration` | `biodiversity_survey` | `community_development` | `fire_prevention` | `forest_protection`

### `GET /projects/{id}/activities`
### `GET /projects/{id}/activities/{aid}`
### `POST /projects/{id}/activities` — Admin Only
```json
{
  "activity_type": "planting",
  "activity_date": "2026-08-22",
  "location_geojson": { "type": "Point", "coordinates": [108.5, -1.5] },
  "target": 10000,
  "realization": 8500,
  "unit": "trees",
  "executor": "Tim Lapangan A",
  "photo_urls": ["http://localhost:8000/static/uploads/foto1.jpg"],
  "notes": "Penanaman di zona 3"
}
```

---

## 🌳 4. TREE RECORDS — Monitoring Pohon

### `GET /projects/{id}/trees`
### `GET /projects/{id}/trees/summary`
```json
{
  "trees_planted": 125430,
  "trees_survived": 114643,
  "trees_dead": 10787,
  "survival_rate": 91.4,
  "alert_triggered": false
}
```
> `alert_triggered: true` = survival rate < 70%, ada alert aktif.

### `POST /projects/{id}/trees` — Admin Only
**Setelah POST, sistem otomatis cek survival rate dan buat alert jika < 70%.**
```json
{
  "plot_id": "WK-023",
  "species": "Shorea balangeran",
  "quantity": 500,
  "planting_date": "2026-08-01",
  "location_geojson": { "type": "Point", "coordinates": [108.5, -1.5] },
  "condition": "healthy",
  "height_cm": 45.5,
  "dbh_cm": 3.2,
  "is_alive": true,
  "photo_urls": ["http://..."],
  "notes": "Batch pertama plot WK-023"
}
```
**`condition` yang valid:** `healthy` | `stressed` | `dead`

### `PUT /projects/{id}/trees/{tid}` — Admin Only
Update kondisi pohon (monitoring berkala). Semua field opsional.
**Setelah PUT, juga auto-cek survival rate.**

---

## 📱 5. FIELD REPORTS — Laporan Lapangan

### `GET /projects/{id}/field-reports`
### `GET /projects/{id}/field-reports/{fid}`
### `POST /projects/{id}/field-reports` — Semua user login bisa
```json
{
  "officer_name": "Andi Prasetyo",
  "plot_id": "WK-023",
  "location_geojson": { "type": "Point", "coordinates": [108.512, -1.534] },
  "report_date": "2026-08-22T09:30:00",
  "report_type": "tree_monitoring",
  "activity_description": "Monitoring kondisi pohon di plot WK-023",
  "result_description": "85 pohon dimonitoring, 3 dalam kondisi stressed",
  "photo_urls": ["http://..."]
}
```
**`report_type` yang valid:**
`tree_monitoring` | `biodiversity` | `incident` | `general` | `community`

---

## 🚨 6. ALERTS — Peringatan

### `GET /projects/{id}/alerts`
Default: hanya alert yang belum resolved.  
`?only_active=false` → tampilkan semua termasuk yang sudah resolved.  
*(Juga auto-trigger cek `monitoring_overdue` setiap dipanggil)*

**Response:**
```json
[
  {
    "id": 1,
    "alert_type": "low_tree_survival",
    "severity": "high",
    "description": "Survival rate pohon turun ke 65.0%...",
    "is_read": false,
    "is_resolved": false,
    "auto_generated": true,
    "created_at": "2026-08-24T07:00:00"
  }
]
```

### `POST /projects/{id}/alerts` — Admin Only
```json
{
  "alert_type": "deforestation",
  "severity": "high",
  "location_geojson": { "type": "Point", "coordinates": [108.5, -1.5] },
  "description": "Terdeteksi pengurangan tutupan hutan di zona utara"
}
```
**`alert_type` yang valid:**
`deforestation` | `fire` | `land_cover_change` | `monitoring_overdue` | `low_tree_survival`

### `PUT /projects/{id}/alerts/{aid}` — Semua user login bisa
```json
{ "is_read": true }
```
atau:
```json
{ "is_resolved": true }
```
> Saat `is_resolved: true`, field `resolved_at` otomatis terisi timestamp sekarang.

---

## 🦋 7. BIODIVERSITY — Keanekaragaman Hayati

### `GET /projects/{id}/biodiversity`
### `GET /projects/{id}/biodiversity/summary`
```json
{
  "total_observations": 215,
  "unique_species": 187,
  "fauna_count": 143,
  "flora_count": 72
}
```
### `POST /projects/{id}/biodiversity` — Admin Only
```json
{
  "species_name": "Pongo pygmaeus",
  "species_type": "fauna",
  "location_geojson": { "type": "Point", "coordinates": [108.6, -1.4] },
  "observed_date": "2026-08-18",
  "habitat": "Hutan sekunder",
  "observer": "Dr. Sari",
  "photo_url": "http://...",
  "notes": "1 individu dewasa di plot WK-031"
}
```
**`species_type`:** `fauna` | `flora`

---

## 👥 8. COMMUNITY — Dampak Sosial

### `GET /projects/{id}/community`
### `GET /projects/{id}/community/summary`
```json
{
  "total_villages": 12,
  "total_beneficiaries": 2430,
  "total_livelihood_groups": 27,
  "total_employment": 340,
  "total_community_investment": 125000.0
}
```
### `POST /projects/{id}/community` — Admin Only
```json
{
  "village_name": "Desa Mekar Jaya",
  "beneficiary_count": 250,
  "livelihood_groups": 3,
  "employment_count": 45,
  "community_investment": 12000.0,
  "activity_type": "pelatihan",
  "description": "Pelatihan agroforestri untuk petani lokal",
  "date": "2026-08-15"
}
```

---

## 🌿 9. CARBON — Estimasi Karbon

> ⚠️ **Wajib**: Tampilkan data karbon dengan label **"Estimasi Monitoring"**, bukan sebagai verified carbon credit.

### `GET /projects/{id}/carbon`
### `POST /projects/{id}/carbon` — Admin Only
```json
{
  "period_start": "2026-01-01",
  "period_end": "2026-06-30",
  "carbon_stock_tco2e": 3200000.0,
  "biomass_ton": 5800000.0,
  "estimated_co2e": 2900000.0,
  "carbon_change": 150000.0,
  "methodology": "IPCC Tier 2",
  "notes": "Periode semester 1 2026"
}
```

---

## 🤖 Logika Auto-Alert

| Kapan terjadi | Kondisi | Alert Type | Severity |
|---------------|---------|------------|----------|
| POST/PUT `/trees` | Survival rate < 70% | `low_tree_survival` | `high` |
| POST/PUT `/trees` | Survival rate < 50% | `low_tree_survival` | `critical` |
| GET `/alerts` atau `/dashboard` | Tidak ada field report > 30 hari | `monitoring_overdue` | `medium` |

> Alert auto tidak duplikat — sistem tidak buat alert baru kalau tipe yang sama sudah aktif.

---

## 🔐 Ringkasan Hak Akses

| Endpoint | `admin`/`super_admin` | `client` |
|----------|-----------------------|---------|
| Buat/edit/hapus proyek | ✅ | ❌ |
| Buat activities, trees, biodiversity, community, carbon, alert | ✅ | ❌ |
| Lihat semua data | ✅ | ✅ |
| Submit field report | ✅ | ✅ |
| Mark alert read/resolved | ✅ | ✅ |

---

## 💻 Contoh Kode JavaScript

### Fetch Dashboard
```javascript
async function getProjectDashboard(projectId, token) {
  const res = await fetch(`http://localhost:8000/api/v1/projects/${projectId}/dashboard`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  return await res.json();
}
```

### Submit Field Report
```javascript
async function submitFieldReport(projectId, data, token) {
  const res = await fetch(`http://localhost:8000/api/v1/projects/${projectId}/field-reports`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      officer_name: data.officerName,
      plot_id: data.plotId,
      location_geojson: { type: "Point", coordinates: [data.lng, data.lat] },
      report_date: new Date().toISOString(),
      report_type: data.reportType,
      activity_description: data.activityDesc,
      result_description: data.resultDesc,
      photo_urls: data.photoUrls ?? []
    })
  });
  return await res.json();
}
```

### Mark Alert Resolved
```javascript
async function resolveAlert(projectId, alertId, token) {
  const res = await fetch(
    `http://localhost:8000/api/v1/projects/${projectId}/alerts/${alertId}`,
    {
      method: 'PUT',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ is_resolved: true })
    }
  );
  return await res.json();
}
```
