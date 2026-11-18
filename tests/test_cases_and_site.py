import json
import tempfile
import unittest
from pathlib import Path

from src.cases import load_cases, safe_url
from src.build_site import render_html, build

ROOT = Path(__file__).resolve().parent.parent


class CasesTests(unittest.TestCase):
    def test_demo_valid(self):
        cases = load_cases(ROOT / 'data/cases.json')
        self.assertEqual(len(cases['cases']), 3)

    def test_safe_url(self):
        self.assertTrue(safe_url('https://data.gov.il/test'))
        self.assertFalse(safe_url('javascript:alert(1)'))
        self.assertFalse(safe_url('https://some.test/\nother'))

    def test_reject_unsupported_real_evidence(self):
        data = load_cases(ROOT / 'data/cases.json')
        data['dataset_type'] = 'real'
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'cases.json'
            path.write_text(json.dumps(data, ensure_ascii=False))
            with self.assertRaisesRegex(ValueError, 'Real datasets'):
                load_cases(path)

    def test_reject_documented_without_sources(self):
        data = load_cases(ROOT / 'data/cases.json')
        data['cases'][0]['evidence_status'] = 'documented'
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'cases.json'
            path.write_text(json.dumps(data, ensure_ascii=False))
            with self.assertRaisesRegex(ValueError, 'cited sources'):
                load_cases(path)

    def test_html_escapes_untrusted_case_content(self):
        data = load_cases(ROOT / 'data/cases.json')
        data['cases'][0]['title'] = '<script>alert("x")</script>'
        html = render_html(data, [])
        self.assertNotIn('<script>alert("x")</script>', html)
        self.assertIn('&lt;script&gt;', html)

    def test_site_build_outputs_assets_and_report(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / 'index.html'
            build(ROOT / 'data/example_observations.csv', ROOT / 'data/cases.json', out)
            self.assertIn('נתוני הדגמה', out.read_text())
            self.assertTrue((out.parent / 'assets/style.css').exists())
            self.assertTrue((out.parent / 'assets/app.js').exists())
            data = json.loads((out.parent / 'report.json').read_text())
            self.assertEqual(data['observation_count'], 3)
            self.assertEqual(data['dataset_type'], 'synthetic')


if __name__ == '__main__':
    unittest.main()
