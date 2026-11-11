import json
import subprocess
import sys
from pathlib import Path

import pytest

from migration_planner.cli import main

ROOT = Path(__file__).resolve().parent.parent
EX = ROOT / "examples"
AS_OF = "2026-11-11"
PLAN_ARGS = ["plan", str(EX / "inventory.csv"), "--assumptions", str(EX / "cost-assumptions.json"), "--as-of", AS_OF]


def read_all(directory: Path) -> dict:
    return {p.name: p.read_bytes() for p in sorted(directory.iterdir())}


@pytest.fixture(scope="module")
def plan_out(tmp_path_factory):
    out = tmp_path_factory.mktemp("plan")
    assert main(PLAN_ARGS + ["--out", str(out)]) == 0
    return out


def test_plan_writes_every_expected_file(plan_out):
    assert sorted(p.name for p in plan_out.iterdir()) == sorted([
        "assessment.csv", "assessment.json", "cost_by_app.csv", "cost_monthly.csv", "cost_summary.csv",
        "plan.json", "plan.md", "sensitivity.csv", "waves.csv", "waves.mmd",
    ])


def test_plan_matches_the_committed_example_output(plan_out):
    committed = EX / "output"
    assert committed.is_dir(), "run the plan command from the README to create examples/output"
    assert read_all(plan_out) == read_all(committed)


def test_plan_is_byte_identical_across_runs(plan_out, tmp_path):
    assert main(PLAN_ARGS + ["--out", str(tmp_path)]) == 0
    assert read_all(tmp_path) == read_all(plan_out)


def test_the_example_shows_each_feature_the_brief_asks_for(plan_out):
    doc = json.loads((plan_out / "plan.json").read_text(encoding="utf-8"))
    apps = {a["app_id"]: a for a in doc["assessment"]["apps"]}
    assert len(apps) == 42
    assert apps["APP012"]["disposition"] == "retain" and apps["APP012"]["in_scope"] is False  # SaaS already in use
    assert apps["APP021"]["end_of_support_date"] == "2020-01-14" and apps["APP021"]["eos_status"] == "past"  # unsupported OS
    assert apps["APP035"]["vendor_supported_in_cloud"] == "unknown" and apps["APP035"]["needs_review"]
    assert apps["APP009"]["disposition"] == "replatform"  # database past extended support
    cycles = {c["group"]: c["apps"] for c in doc["waves"]["cycles"]}
    assert cycles == {"CYC-1": ["APP026", "APP027"], "CYC-2": ["APP032", "APP033", "APP034"]}
    placement = doc["waves"]["placement"]
    assert all(placement[i]["wave"] >= 2 for i, a in apps.items() if i in placement and a["business_criticality"] >= 4)
    assert placement["APP001"]["wave"] == 2  # shared service, critical, so after the pilot wave
    for a in apps.values():
        for d in a["dependencies"]:
            if a["app_id"] in placement and d in placement and placement[a["app_id"]]["cycle_group"] != placement[d]["cycle_group"]:
                assert placement[d]["wave"] < placement[a["app_id"]]["wave"]


def test_plan_markdown_has_the_required_sections(plan_out):
    text = (plan_out / "plan.md").read_text(encoding="utf-8")
    for heading in ("## Summary", "## Decisions that need a human", "## Waves", "## Cost comparison", "### Sensitivity",
                    "### What is not modelled", "## Appendix: reasons for every decision"):
        assert heading in text
    assert "Illustrative cost assumptions" in text and "Planning aid only" in text


def test_commands_chain_through_assessment_json(tmp_path, plan_out):
    a = tmp_path / "a"
    assert main(["assess", str(EX / "inventory.csv"), "--as-of", AS_OF, "--out", str(a)]) == 0
    w = tmp_path / "w"
    assert main(["waves", str(a / "assessment.json"), "--out", str(w)]) == 0
    c = tmp_path / "c"
    assert main(["cost", str(a / "assessment.json"), "--assumptions", str(EX / "cost-assumptions.json"), "--out", str(c)]) == 0
    assert (w / "waves.csv").read_bytes() == (plan_out / "waves.csv").read_bytes()
    assert (c / "cost_summary.csv").read_bytes() == (plan_out / "cost_summary.csv").read_bytes()
    assert (a / "assessment.csv").read_bytes() == (plan_out / "assessment.csv").read_bytes()


def test_wave_size_option(tmp_path):
    assert main(["waves", str(EX / "inventory.csv"), "--as-of", AS_OF, "--max-wave-size", "4", "--out", str(tmp_path)]) == 0
    doc = json.loads((tmp_path / "waves.json").read_text(encoding="utf-8"))
    assert doc["settings"]["max_wave_size"] == 4
    assert max(w["size"] for w in doc["waves"] if not w["cycle_groups"]) <= 4


def test_fail_on_cycles_exit_status(tmp_path):
    args = ["waves", str(EX / "inventory.csv"), "--as-of", AS_OF, "--out", str(tmp_path)]
    assert main(args) == 0
    assert main(args + ["--fail-on-cycles"]) == 3


def test_overrides_flow_through_the_plan(tmp_path):
    assert main(PLAN_ARGS + ["--overrides", str(EX / "overrides.example.csv"), "--out", str(tmp_path)]) == 0
    doc = json.loads((tmp_path / "plan.json").read_text(encoding="utf-8"))
    apps = {a["app_id"]: a for a in doc["assessment"]["apps"]}
    assert apps["APP021"]["disposition"] == "retire" and apps["APP021"]["overridden"] is True
    assert apps["APP035"]["disposition"] == "retain"
    assert "APP035" not in doc["waves"]["placement"]


def test_bad_inventory_exits_with_status_2_and_lists_problems(tmp_path, capsys):
    bad = tmp_path / "bad.csv"
    bad.write_text("app_id,name\nA1,x\n", encoding="utf-8")
    assert main(["assess", str(bad), "--out", str(tmp_path / "o")]) == 2
    err = capsys.readouterr().err
    assert "missing column(s)" in err and "error:" in err
    assert not (tmp_path / "o").exists()


def test_unfilled_template_stops_the_cost_command(tmp_path, capsys):
    main(["show-assumptions-template"])
    template = capsys.readouterr().out
    t = tmp_path / "template.json"
    t.write_text(template, encoding="utf-8")
    assert main(["cost", str(EX / "inventory.csv"), "--assumptions", str(t), "--as-of", AS_OF, "--out", str(tmp_path / "o")]) == 2
    assert "is empty. Supply a value" in capsys.readouterr().err


def test_missing_files_give_readable_errors(tmp_path, capsys):
    assert main(["assess", str(tmp_path / "nope.csv")]) == 2
    assert "not found" in capsys.readouterr().err
    assert main(["waves", str(EX / "inventory.csv"), "--as-of", "yesterday", "--out", str(tmp_path)]) == 2
    assert "--as-of" in capsys.readouterr().err
    assert main(["waves", str(EX / "inventory.csv"), "--rules", str(tmp_path / "r.json")]) == 2
    j = tmp_path / "notassessment.json"
    j.write_text("{}", encoding="utf-8")
    assert main(["waves", str(j)]) == 2
    assert "not an assessment file" in capsys.readouterr().err


def test_show_rules_round_trips(tmp_path, capsys):
    main(["show-rules"])
    text = capsys.readouterr().out
    rules_file = tmp_path / "rules.json"
    rules_file.write_text(text, encoding="utf-8")
    one, two = tmp_path / "one", tmp_path / "two"
    assert main(["assess", str(EX / "inventory.csv"), "--as-of", AS_OF, "--out", str(one)]) == 0
    assert main(["assess", str(EX / "inventory.csv"), "--as-of", AS_OF, "--rules", str(rules_file), "--out", str(two)]) == 0
    assert read_all(one) == read_all(two)


def test_the_module_runs_from_the_command_line(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "migration_planner", "assess", str(EX / "inventory.csv"), "--as-of", AS_OF, "--out", str(tmp_path)],
        capture_output=True, text=True, cwd=ROOT,
    )
    assert result.returncode == 0, result.stderr
    assert "Assessed 42 applications" in result.stdout
    version = subprocess.run([sys.executable, "-m", "migration_planner", "--version"], capture_output=True, text=True, cwd=ROOT)
    assert version.stdout.startswith("migration_planner ")


def test_input_row_order_does_not_change_the_output(tmp_path):
    lines = (EX / "inventory.csv").read_text(encoding="utf-8").splitlines()
    shuffled = tmp_path / "inventory.csv"
    shuffled.write_text("\n".join([lines[0], *reversed(lines[1:])]) + "\n", encoding="utf-8")
    a, b = tmp_path / "a", tmp_path / "b"
    assert main(["waves", str(EX / "inventory.csv"), "--as-of", AS_OF, "--out", str(a)]) == 0
    assert main(["waves", str(shuffled), "--as-of", AS_OF, "--out", str(b)]) == 0
    for name in ("waves.csv", "waves.mmd"):
        assert (a / name).read_bytes() == (b / name).read_bytes()
