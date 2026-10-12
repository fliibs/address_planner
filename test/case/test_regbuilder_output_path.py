"""Exercise the real Excel CLI without adding an extra output directory."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class RegbuilderOutputPathTest(unittest.TestCase):
    def test_default_and_explicit_output(self):
        environment = os.environ.copy()
        environment["ADDRESS_PLANNER_ROOT"] = str(PROJECT_ROOT)
        fixture = PROJECT_ROOT / "excel/excel_demo/regbank_demo.xlsx"
        with tempfile.TemporaryDirectory(prefix="regbuilder_output_") as scratch:
            for label, args in (("build", []), ("custom", ["-o", "custom"])):
                with self.subTest(output=label):
                    cwd = Path(scratch) / label
                    cwd.mkdir()
                    result = subprocess.run(
                        [sys.executable, str(PROJECT_ROOT / "regbuilder.py"),
                         "-e", str(fixture), *args],
                        cwd=cwd, env=environment, text=True,
                        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                        timeout=120,
                    )
                    self.assertEqual(result.returncode, 0, result.stdout)
                    output = cwd / label
                    report = json.loads(result.stdout.splitlines()[-1])
                    self.assertEqual(Path(report["generated_root"]), output)
                    self.assertEqual(Path(report["script"]).parent, output)
                    bank_dir = output / "reg_bank_table"
                    self.assertTrue(list((bank_dir / "rtl").rglob("*.v")))
                    self.assertTrue((bank_dir / "html/reg_bank_table_address_map.html").is_file())
                    self.assertFalse((output / "generated").exists())
                    self.assertFalse((bank_dir / "reg_bank_table").exists())


if __name__ == "__main__":
    unittest.main()
