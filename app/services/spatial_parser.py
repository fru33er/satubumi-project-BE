import os
import zipfile
import tempfile
import json
from typing import Tuple, Dict, Any, Optional
import shapefile
from shapely.geometry import shape, mapping
from shapely.validation import make_valid
from shapely.ops import unary_union, transform
import pyproj

def _detect_source_crs(shp_path: str) -> pyproj.CRS:
    """
    Mendeteksi CRS sumber dari file .prj yang menyertai shapefile.
    Menggunakan beberapa strategi fallback untuk menangani file .prj
    yang tidak standar atau mengandung typo (mis. 'GCS_WGS984' vs 'GCS_WGS_1984').

    Urutan deteksi:
    1. Parse langsung dengan pyproj
    2. Fuzzy match keyword WGS84 → EPSG:4326
    3. Fuzzy match UTM zona Indonesia → EPSG yang sesuai
    4. Fallback ke EPSG:4326 (WGS84)
    """
    prj_path = shp_path.replace(".shp", ".prj")
    if not os.path.exists(prj_path):
        return pyproj.CRS('EPSG:4326')

    with open(prj_path, 'r', errors='replace') as f:
        prj_text = f.read().strip()

    # Strategi 1: Parse langsung dengan pyproj
    try:
        return pyproj.CRS(prj_text)
    except pyproj.exceptions.CRSError:
        pass

    prj_upper = prj_text.upper()

    # Strategi 2: Fuzzy match WGS84 — tangani typo seperti "WGS984", "WGS1984"
    wgs84_keywords = ['WGS84', 'WGS_1984', 'WGS 1984', 'WGS984', 'D_WGS', 'GCS_WGS']
    if any(kw in prj_upper for kw in wgs84_keywords):
        return pyproj.CRS('EPSG:4326')

    # Strategi 3: Deteksi UTM zona Indonesia (46–54)
    if 'UTM' in prj_upper or 'TRANSVERSE_MERCATOR' in prj_upper:
        for zone_num in range(46, 55):
            if str(zone_num) in prj_text:
                is_south = 'SOUTH' in prj_upper or 'SELATAN' in prj_upper
                epsg_code = (32700 + zone_num) if is_south else (32600 + zone_num)
                try:
                    return pyproj.CRS(f'EPSG:{epsg_code}')
                except Exception:
                    pass

    # Strategi 4: Fallback ke WGS84
    return pyproj.CRS('EPSG:4326')


def _select_best_shp(shp_paths: list, polygon_types: set) -> str:
    """
    Memilih file .shp terbaik dari daftar kandidat.

    Strategi:
    1. Filter hanya shapefile bertipe polygon (shapeType 5/15/25)
    2. Di antara polygon, pilih yang bounding box-nya terluas (luas = dx * dy)
       — ini memilih batas kawasan/administrasi utama, bukan layer jalan/titik
    3. Jika tidak ada polygon, fallback ke file dengan ukuran terbesar
    """
    best_polygon = None
    best_bbox_area = -1.0

    for shp_path in shp_paths:
        try:
            with shapefile.Reader(shp_path) as sf:
                if sf.shapeType not in polygon_types:
                    continue
                bbox = sf.bbox  # (xmin, ymin, xmax, ymax)
                bbox_area = abs(bbox[2] - bbox[0]) * abs(bbox[3] - bbox[1])
                if bbox_area > best_bbox_area:
                    best_bbox_area = bbox_area
                    best_polygon = shp_path
        except Exception:
            continue

    if best_polygon:
        return best_polygon

    # Fallback: tidak ada polygon → pilih file terbesar
    return max(shp_paths, key=os.path.getsize)


def parse_shapefile_zip(zip_bytes: bytes) -> Tuple[Dict[str, Any], float]:
    """
    Mengekstrak file ZIP yang berisi berkas ESRI Shapefile (.shp, .shx, .dbf, .prj),
    membaca geometri menggunakan PyShp (Pure Python), meretransformasi CRS ke WGS84,
    dan menghitung luas area dalam hektare (ha).
    """
    with tempfile.TemporaryDirectory() as tmpdirname:
        zip_path = os.path.join(tmpdirname, "uploaded_shapefile.zip")
        with open(zip_path, "wb") as f:
            f.write(zip_bytes)
            
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(tmpdirname)
            
        # Kumpulkan semua .shp di dalam ZIP
        shp_candidates = []
        for root, _, files in os.walk(tmpdirname):
            for file in files:
                if file.lower().endswith(".shp"):
                    shp_candidates.append(os.path.join(root, file))

        if not shp_candidates:
            raise ValueError("Tidak ditemukan file .shp di dalam file ZIP yang diunggah.")

        # Pilih SHP terbaik: polygon area dengan bounding box terluas
        # shapeType polygon: 5 (Polygon), 15 (PolygonZ), 25 (PolygonM)
        POLYGON_TYPES = {5, 15, 25}
        shp_file = _select_best_shp(shp_candidates, POLYGON_TYPES)

        # Deteksi CRS sumber dari file .prj
        source_crs = _detect_source_crs(shp_file)

        # Membaca shapefile dan memastikan file handle (.shp, .shx, .dbf) ditutup rapat
        with shapefile.Reader(shp_file) as sf:
            shapes = sf.shapes()
            if not shapes:
                raise ValueError("File Shapefile tidak berisi geometri yang valid.")
            geoms = [make_valid(shape(s.__geo_interface__)) for s in shapes if s]
            
        if not geoms:
            raise ValueError("Geometri di dalam Shapefile kosong.")
            
        unified_geom = geoms[0] if len(geoms) == 1 else unary_union(geoms)
        
        # Transformasi ke WGS84 jika bukan WGS84
        if source_crs != pyproj.CRS('EPSG:4326'):
            project = pyproj.Transformer.from_crs(source_crs, pyproj.CRS('EPSG:4326'), always_xy=True).transform
            unified_geom = transform(project, unified_geom)
        
        # Hitung luas area dalam Hektare menggunakan proyeksi equal-area (World Cylindrical Equal Area EPSG:6933)
        proj_wgs84 = pyproj.CRS('EPSG:4326')
        proj_equal = pyproj.CRS('EPSG:6933')
        transformer = pyproj.Transformer.from_crs(proj_wgs84, proj_equal, always_xy=True)
        
        equal_geom = transform(transformer.transform, unified_geom)
        area_m2 = equal_geom.area
        area_ha = round(area_m2 / 10000.0, 2)
        
        if area_ha <= 0:
            raise ValueError("Luas area tidak valid (nol atau negatif).")
        
        return mapping(unified_geom), area_ha

def parse_geojson(geojson_input: str) -> Tuple[Dict[str, Any], float]:
    """
    Memuat string / dict GeoJSON, memvalidasi poligon, dan menghitung luas area dalam hektare.
    """
    if isinstance(geojson_input, str):
        data = json.loads(geojson_input)
    else:
        data = geojson_input
        
    geom_shape = shape(data if "geometry" not in data else data["geometry"])
    geom_shape = make_valid(geom_shape)
    
    proj_wgs84 = pyproj.CRS('EPSG:4326')
    proj_equal = pyproj.CRS('EPSG:6933')
    transformer = pyproj.Transformer.from_crs(proj_wgs84, proj_equal, always_xy=True)
    
    equal_geom = transform(transformer.transform, geom_shape)
    area_m2 = equal_geom.area
    area_ha = round(area_m2 / 10000.0, 2)
    
    if area_ha <= 0:
        raise ValueError("Luas area tidak valid (nol atau negatif).")
    
    return mapping(geom_shape), area_ha
