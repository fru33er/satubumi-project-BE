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


if __name__ == "__main__":
    unittest.main()
