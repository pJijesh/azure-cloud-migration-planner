import csv
import sys
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from migration_planner.assess import assess_all  # noqa: E402
from migration_planner.inventory import load_inventory  # noqa: E402
from migration_planner.rules import load_rules  # noqa: E402

HEADER = [
    "app_id", "name", "owner", "business_criticality", "users", "technology", "os_or_platform",
    "end_of_support_date", "vendor_supported_in_cloud", "data_sensitivity", "dependencies",
    "current_annual_cost", "change_frequency", "licence_model", "notes",
]
AS_OF = date(2026, 11, 11)


def row(app_id, **kw):
    base = {
        "app_id": app_id, "name": f"App {app_id}", "owner": "Owner", "business_criticality": "3", "users": "50",
        "technology": "Packaged application", "os_or_platform": "Windows Server 2022",
        "end_of_support_date": "2031-10-14", "vendor_supported_in_cloud": "yes", "data_sensitivity": "low",
        "dependencies": "", "current_annual_cost": "12000", "change_frequency": "low",
        "licence_model": "subscription", "notes": "",
    }
    base.update({k: str(v) for k, v in kw.items()})
    return base


def write_csv(path, rows, header=None):
    header = header or HEADER
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=header, lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow(r)
    return path


@pytest.fixture
def rules():
    return load_rules()


@pytest.fixture
def make_assessed(tmp_path, rules):
    def _make(rows, as_of=AS_OF):
        p = write_csv(tmp_path / "inv.csv", rows)
        apps, _ = load_inventory(p)
        return assess_all(apps, rules, as_of)

    return _make


@pytest.fixture
def make_inventory(tmp_path):
    def _make(rows, name="inv.csv"):
        return write_csv(tmp_path / name, rows)

    return _make
