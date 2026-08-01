import os
import zipfile
import tempfile
import json
from typing import Tuple, Dict, Any
import shapefile
from shapely.geometry import shape, mapping
from shapely.validation import make_valid
from shapely.ops import unary_union, transform
import pyproj

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
            
        shp_file = None
        for root, _, files in os.walk(tmpdirname):
            for file in files:
                if file.lower().endswith(".shp"):
                    shp_file = os.path.join(root, file)
                    break
            if shp_file:
                break
                    
        if not shp_file:
            raise ValueError("Tidak ditemukan file .shp di dalam file ZIP yang diunggah.")
            
        # Membaca shapefile dan memastikan file handle (.shp, .shx, .dbf) ditutup rapat
        with shapefile.Reader(shp_file) as sf:
            shapes = sf.shapes()
            if not shapes:
                raise ValueError("File Shapefile tidak berisi geometri yang valid.")
            geoms = [make_valid(shape(s.__geo_interface__)) for s in shapes if s]
            
        if not geoms:
            raise ValueError("Geometri di dalam Shapefile kosong.")
            
        unified_geom = geoms[0] if len(geoms) == 1 else unary_union(geoms)
        
        # Hitung luas area dalam Hektare menggunakan proyeksi equal-area (World Cylindrical Equal Area EPSG:6933)
        proj_wgs84 = pyproj.CRS('EPSG:4326')
        proj_equal = pyproj.CRS('EPSG:6933')
        transformer = pyproj.Transformer.from_crs(proj_wgs84, proj_equal, always_xy=True)
        
        equal_geom = transform(transformer.transform, unified_geom)
        area_m2 = equal_geom.area
        area_ha = round(area_m2 / 10000.0, 2)
        
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
    
    return mapping(geom_shape), area_ha
