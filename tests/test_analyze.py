import math
import tempfile
import unittest
from pathlib import Path
from src.analyze import rank, load_observations


def observation(**kwargs):
    row = dict(site_id='A', date='2026-01-01', period='AM',
               observed_minutes='10', freeflow_minutes='5', vehicles='10', source='synthetic')
    row.update(kwargs)
    return row


class AnalyzeTests(unittest.TestCase):
    def test_rank_and_order(self):
        ranked = rank([observation(), observation(site_id='B', vehicles='20')])
        self.assertEqual([item['site_id'] for item in ranked], ['B', 'A'])
        self.assertEqual(ranked[0]['excess_vehicle_minutes'], 100)

    def test_reject_negative_delay(self):
        with self.assertRaises(ValueError):
            rank([observation(observed_minutes='4')])

    def test_bad_numeric_inputs(self):
        for value in ('nan', 'Infinity', '-10', '3.2'):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    rank([observation(vehicles=value)])

    def test_missing_or_bad_identifiers(self):
        for kwargs in (dict(source=''), dict(date='tomorrow'), dict(site_id='')):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                rank([observation(**kwargs)])

    def test_duplicate_window_is_rejected(self):
        with self.assertRaises(ValueError):
            rank([observation(), observation()])

    def test_reject_csv_duplicate_column_names(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'data.csv'
            path.write_text('site_id,site_id,date\nA,A,2026-01-01\n')
            with self.assertRaisesRegex(ValueError, 'duplicate columns'):
                load_observations(path)
