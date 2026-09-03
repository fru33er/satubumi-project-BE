import unittest

from app.schemas.rapid_fs import RapidFSInput
from app.services.rapid_fs_engine import calculate_rapid_fs


class TestRapidFSEngine(unittest.TestCase):
    def test_rapid_fs_calculation_tropical_forest(self):
        """
        Uji simulasi sesuai dokumen Profil Satubumi:
        Area = 50.000 ha, Durasi = 30 tahun, Ekosistem = Hutan Tropis (ER = 5 tCO2e/ha/thn),
        Harga Karbon = USD 10/tCO2e.
        """
        input_data = RapidFSInput(
            location_name="Hutan Kalimantan Test",
            area_ha=50000.0,
            ecosystem_type="hutan_tropis",
            project_duration_years=30,
            carbon_price_usd=10.0,
        )

        result = calculate_rapid_fs(input_data)

        self.assertEqual(result.area_ha, 50000.0)
        self.assertEqual(
            result.acc_total_credits, 7500000.0
        )  # 50k * 5 * 30 = 7.5M tCO2e
        self.assertEqual(result.gross_revenue_usd, 75000000.0)  # 7.5M * 10 = 75M USD
        self.assertGreaterEqual(result.feasibility_score, 60.0)
        self.assertIn(result.feasibility_category, ["Potensi Sedang", "Potensi Tinggi"])

    def test_rapid_fs_mangrove_ecosystem(self):
        input_data = RapidFSInput(
            location_name="Mangrove Papua Test",
            area_ha=10000.0,
            ecosystem_type="mangrove",
            project_duration_years=30,
            carbon_price_usd=12.0,
        )

        result = calculate_rapid_fs(input_data)

        self.assertEqual(
            result.emission_reduction_rate, 10.0
        )  # Mangrove rate 10 tCO2e/ha/yr
        self.assertEqual(result.acc_total_credits, 3000000.0)  # 10k * 10 * 30 = 3M
        self.assertEqual(result.gross_revenue_usd, 36000000.0)  # 3M * 12 = 36M USD
        self.assertEqual(result.feasibility_category, "Potensi Tinggi")

    def test_gee_extract_spatial_metrics_fallback_mock(self):
        from app.services.gee_service import gee_service
        dummy_polygon = {
            "type": "Polygon",
            "coordinates": [[[110.0, -7.0], [110.1, -7.0], [110.1, -7.1], [110.0, -7.1], [110.0, -7.0]]]
        }
        spatial_metrics = gee_service.extract_spatial_metrics(dummy_polygon, 1500.0)
        self.assertIsNotNone(spatial_metrics)
        self.assertIn("spatial_overlay_layers", spatial_metrics)
        self.assertIn("1_tutupan_lahan", spatial_metrics["spatial_overlay_layers"])
        self.assertIn("2_ndvi", spatial_metrics["spatial_overlay_layers"])
        self.assertIn("cf", spatial_metrics)
        self.assertIn("er", spatial_metrics)

    def test_rapid_fs_with_spatial_override(self):
        from app.services.gee_service import gee_service
        input_data = RapidFSInput(
            location_name="Spatial Mode Test",
            area_ha=2000.0,
            ecosystem_type="hutan_tropis",
            project_duration_years=30,
            carbon_price_usd=10.0,
            polygon_geojson={
                "type": "Polygon",
                "coordinates": [[[110.0, -7.0], [110.1, -7.0], [110.1, -7.1], [110.0, -7.1], [110.0, -7.0]]]
            }
        )
        spatial_metrics = gee_service.extract_spatial_metrics(input_data.polygon_geojson, input_data.area_ha)
        result = calculate_rapid_fs(input_data, spatial_override=spatial_metrics)
        self.assertEqual(result.area_ha, 2000.0)
        self.assertIsNotNone(result.spatial_overlay_layers)
        self.assertIn("1_tutupan_lahan", result.spatial_overlay_layers)


if __name__ == "__main__":
    unittest.main()
