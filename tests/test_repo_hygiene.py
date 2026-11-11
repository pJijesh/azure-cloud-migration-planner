"""Documentation and repository checks: links resolve, generated docs are current, no stray characters."""

import csv
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
TEXT_SUFFIXES = {".md", ".py", ".json", ".csv", ".mmd", ".yml", ".toml", ".txt", ".gitignore", ".gitattributes", ".svg", ""}
SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", "node_modules", "migration_planner.egg-info", "azure_cloud_migration_planner.egg-info"}
# Built from fragments so that this file does not trip its own check.
FORBIDDEN = [
    "I" + "CL", "International " + "Cargo", "Ment" + "field", "As" + "com", "Trans " + "Data", "T" + "DM", "Digi" + "change", "Dew" + "hurst",
    "Sys" + "pro", "Help" + "Hub", "Ha" + "yes", "Fel" + "tham", "Pais" + "ley", "Heath" + "row", "Mon" + "dial", "S" + "KAI", "fract" + "ional",
    "C" + "TO", "Cla" + "ude", "Anthro" + "pic", "AI-" + "generated", "co-" + "author", "Cargo" + "Wise",
]
DASHES = [chr(0x2014), chr(0x2013)]


def text_files():
    for p in sorted(ROOT.rglob("*")):
        if p.is_file() and not (set(p.relative_to(ROOT).parts) & SKIP_DIRS) and p.suffix in TEXT_SUFFIXES and p.suffix != ".png":
            yield p


def test_no_em_or_en_dashes_anywhere():
    bad = [str(p.relative_to(ROOT)) for p in text_files() if any(d in p.read_text(encoding="utf-8") for d in DASHES)]
    assert bad == []


def test_no_forbidden_strings():
    hits = []
    for p in text_files():
        text = p.read_text(encoding="utf-8")
        for word in FORBIDDEN:
            pattern = r"\b" + re.escape(word) + r"\b" if word.isupper() and len(word) <= 4 else re.escape(word)
            if re.search(pattern, text, re.IGNORECASE if len(word) > 4 else 0):
                hits.append(f"{p.relative_to(ROOT)}: {word}")
    assert hits == []


def test_markdown_relative_links_resolve():
    broken = []
    for md in ROOT.rglob("*.md"):
        if set(md.relative_to(ROOT).parts) & SKIP_DIRS:
            continue
        for target in re.findall(r"\]\(([^)\s]+)\)", md.read_text(encoding="utf-8")):
            if re.match(r"^(https?:|mailto:|#)", target):
                continue
            path = target.split("#")[0]
            if path and not (md.parent / path).exists():
                broken.append(f"{md.relative_to(ROOT)} -> {target}")
    assert broken == []


def test_generated_documentation_is_current():
    result = subprocess.run([sys.executable, str(ROOT / "tools" / "build_docs.py"), "--check"], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


def test_every_rule_appears_in_the_rules_document():
    doc = (ROOT / "docs" / "disposition-rules.md").read_text(encoding="utf-8")
    rules = json.loads((ROOT / "migration_planner" / "default_rules.json").read_text(encoding="utf-8"))["rules"]
    for r in rules:
        assert f"| {r['id']} |" in doc


def test_checklist_csv_is_well_formed_and_covers_the_required_topics():
    with open(ROOT / "docs" / "landing-zone-readiness.csv", newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    ids = [r["id"] for r in rows]
    assert len(ids) == len(set(ids))
    areas = {r["area"] for r in rows}
    for needed in ("Identity", "Network", "Governance", "Security", "Monitoring", "Backup and DR", "Cost management"):
        assert needed in areas
    assert all(r["check"] and r["why_it_matters"] and r["evidence_to_collect"] for r in rows)
    assert {r["needed_before"] for r in rows} <= {"pilot wave", "first production wave", "each wave", "programme end"}
    md = (ROOT / "docs" / "landing-zone-readiness.md").read_text(encoding="utf-8")
    assert all(f"**{i}**" in md for i in ids)


@pytest.mark.parametrize("name", ["overview", "decision-flow", "wave-example"])
def test_diagram_sources_have_rendered_images(name):
    d = ROOT / "docs" / "diagrams"
    assert (d / f"{name}.mmd").is_file() and (d / f"{name}.svg").stat().st_size > 1000 and (d / f"{name}.png").stat().st_size > 1000


def test_wave_example_diagram_matches_the_tool_output(tmp_path):
    from migration_planner.cli import main

    assert main(["waves", str(ROOT / "docs" / "diagrams" / "wave-example.csv"), "--as-of", "2026-11-11", "--max-wave-size", "4", "--out", str(tmp_path)]) == 0
    assert (tmp_path / "waves.mmd").read_text(encoding="utf-8") == (ROOT / "docs" / "diagrams" / "wave-example.mmd").read_text(encoding="utf-8")


def test_worked_example_quotes_the_real_output():
    plan = json.loads((ROOT / "examples" / "output" / "plan.json").read_text(encoding="utf-8"))
    doc = (ROOT / "docs" / "worked-example.md").read_text(encoding="utf-8")
    cost = plan["cost"]
    assert f"GBP {cost['stay']['total']:,.0f}" in doc
    assert f"GBP {cost['plan']['total']:,.0f}" in doc
    assert f"GBP {abs(cost['saving']):,.0f} dearer" in doc
    assert f"GBP {cost['stay']['final_year_run_cost']:,.0f}" in doc and f"GBP {cost['plan']['final_year_run_cost']:,.0f}" in doc
    counts = plan["assessment"]["summary"]["by_disposition"]
    for d, n in counts.items():
        assert re.search(rf"\| {d} \| {n} \|", doc), d
    assert f"{plan['assessment']['summary']['needs_review']} of the 42 need a human decision" in doc
    assert plan["waves"]["wave_count"] == 8


def test_required_repository_files_exist():
    for name in ("README.md", "LICENSE", "CONTRIBUTING.md", ".gitignore", ".github/workflows/test.yml", "pyproject.toml"):
        assert (ROOT / name).is_file(), name
    assert "Copyright (c) 2026 Jijesh Puliyappottammal" in (ROOT / "LICENSE").read_text(encoding="utf-8")


def test_package_has_no_third_party_imports():
    stdlib = set(sys.stdlib_module_names)
    for p in (ROOT / "migration_planner").glob("*.py"):
        for mod in re.findall(r"^(?:from|import)\s+([a-zA-Z_][\w]*)", p.read_text(encoding="utf-8"), re.MULTILINE):
            assert mod in stdlib or mod in ("migration_planner", "__future__"), f"{p.name} imports {mod}"
