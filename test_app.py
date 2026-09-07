"""Run with python -m unittest test_app."""
import tempfile
import unittest
from pathlib import Path

import pandas as pd
from streamlit.testing.v1 import AppTest

from app import DATA_PATH, load_summary, compare_athlete, load_disciplines

APP_PATH = Path(__file__).resolve().parent / 'app.py'


class DashboardTests(unittest.TestCase):
    def test_athlete_selection_and_benchmark_gaps(self):
        source = load_summary()
        app = AppTest.from_file(str(APP_PATH), default_timeout=30).run()
        self.assertFalse(app.exception)
        disciplines = load_disciplines()
        codes = [next(code for code in source.fis_code.unique() if disciplines[code] == discipline)
                 for discipline in ["Women's Moguls", "Men's Moguls"]]
        for code in codes:
            app.selectbox[0].set_value(code).run()
            self.assertFalse(app.exception)
            actual = app.dataframe[0].value
            self.assertEqual(len(actual), 6)
            expected = source.loc[source.fis_code.eq(code)].set_index('round')
            row = actual.loc[actual['round'].eq('Qualification') & actual.jump.eq('Jump 1')].iloc[0]
            self.assertAlmostEqual(row.athlete_mean, expected.loc['Qualification', 'jump_1_degree_diff_mean'])
            benchmark = 0.99171875 if disciplines[code] == "Women's Moguls" else 0.92
            self.assertEqual(row.podium_mean, benchmark)
            self.assertAlmostEqual(row.gap, row.athlete_mean - benchmark)

    def test_missing_round_keeps_benchmark_without_zero(self):
        source = load_summary().iloc[[0]]
        result = compare_athlete(source, source.fis_code.iloc[0], "Women's Moguls")
        self.assertEqual(result.podium_mean.tolist(), [0.99171875, 1.007307692, 1.007308, 0.91359375, 0.931025641, 0.937564])
        absent = result.loc[result['round'].eq('Deciding Final')]
        self.assertTrue(absent.athlete_mean.isna().all())
        self.assertTrue(absent.gap.isna().all())

    def test_missing_means_and_leading_zero_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'summary.csv'
            path.write_text('athlete,fis_code,round,run_count,jump_1_degree_diff_mean,jump_2_degree_diff_mean\nExample,00123,Qualification,2,,0.8\n')
            data = load_summary(path)
            self.assertEqual(data.fis_code.iloc[0], '00123')
            self.assertTrue(pd.isna(data.jump_1_degree_diff_mean.iloc[0]))
            self.assertEqual(data.run_count.iloc[0], 2)

    def test_duplicate_groups_rejected(self):
        source = pd.read_csv(DATA_PATH, dtype={'fis_code': 'string'})
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'summary.csv'
            pd.concat([source, source.iloc[[0]]]).to_csv(path, index=False)
            with self.assertRaisesRegex(ValueError, 'one row per FIS'):
                load_summary(path)


if __name__ == '__main__':
    unittest.main()
