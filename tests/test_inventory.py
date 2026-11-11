import pytest

from conftest import HEADER, row, write_csv
from migration_planner.errors import ValidationError
from migration_planner.inventory import load_inventory


def test_loads_a_valid_inventory(make_inventory):
    p = make_inventory([row("A1", dependencies="A2"), row("A2", users="", current_annual_cost="", end_of_support_date="")])
    apps, warnings = load_inventory(p)
    assert [a.app_id for a in apps] == ["A1", "A2"]
    assert apps[0].dependencies == ("A2",)
    assert apps[1].users is None and apps[1].current_annual_cost is None and apps[1].end_of_support_date is None
    assert warnings == []


def test_currency_symbols_and_commas_are_accepted(make_inventory):
    p = make_inventory([row("A1", current_annual_cost="£12,500")])
    apps, _ = load_inventory(p)
    assert apps[0].current_annual_cost == 12500.0


def test_blank_vendor_support_means_unknown(make_inventory):
    p = make_inventory([row("A1", vendor_supported_in_cloud="")])
    assert load_inventory(p)[0][0].vendor_supported_in_cloud == "unknown"


def test_all_problems_are_reported_together_with_line_numbers(make_inventory):
    p = make_inventory([
        row("A1", business_criticality="9"),
        row("A2", end_of_support_date="31/12/2027"),
        row("A3", vendor_supported_in_cloud="maybe"),
        row("A1"),
        row("A5", users="-3", dependencies="NOPE"),
    ])
    with pytest.raises(ValidationError) as exc:
        load_inventory(p)
    text = "\n".join(exc.value.problems)
    assert "line 2 (A1): business_criticality 9 must be between 1 and 5" in text
    assert "line 3 (A2): end_of_support_date" in text and "YYYY-MM-DD" in text
    assert "line 4 (A3): vendor_supported_in_cloud 'maybe'" in text
    assert "line 5 (A1): app_id 'A1' already used on line 2" in text
    assert "line 6 (A5): users" in text
    assert "dependency 'NOPE' is not in the inventory" in text


def test_unknown_dependency_can_be_downgraded_to_a_warning(make_inventory):
    p = make_inventory([row("A1", dependencies="GHOST;A1")])
    apps, warnings = load_inventory(p, allow_unknown_dependencies=True)
    assert apps[0].dependencies == ()
    assert any("GHOST" in w for w in warnings) and any("itself" in w for w in warnings)


def test_missing_column_is_named(tmp_path):
    header = [h for h in HEADER if h != "owner"]
    p = write_csv(tmp_path / "x.csv", [{k: "1" for k in header}], header)
    with pytest.raises(ValidationError) as exc:
        load_inventory(p)
    assert "missing column(s): owner" in exc.value.problems[0]


def test_empty_and_missing_files(tmp_path):
    (tmp_path / "empty.csv").write_text("", encoding="utf-8")
    with pytest.raises(ValidationError, match="empty"):
        load_inventory(tmp_path / "empty.csv")
    with pytest.raises(ValidationError, match="not found"):
        load_inventory(tmp_path / "nope.csv")
    write_csv(tmp_path / "hdr.csv", [])
    with pytest.raises(ValidationError, match="no applications"):
        load_inventory(tmp_path / "hdr.csv")


def test_byte_order_mark_and_header_case_are_tolerated(tmp_path):
    p = tmp_path / "bom.csv"
    text = ",".join(h.upper() for h in HEADER) + "\n" + ",".join(row("A1").values()) + "\n"
    p.write_text(text, encoding="utf-8-sig")
    assert load_inventory(p)[0][0].app_id == "A1"


def test_unknown_columns_are_reported_not_fatal(tmp_path):
    p = write_csv(tmp_path / "x.csv", [dict(row("A1"), extra="x")], HEADER + ["extra"])
    _, warnings = load_inventory(p)
    assert any("extra" in w for w in warnings)
