import copy

from conftest import row
from migration_planner.graph import shortest_cycle_through, strongly_connected_components
from migration_planner.rules import load_rules
from migration_planner.waves import build_waves, waves_mermaid


def wave_of(plan):
    return {m: p["wave"] for m, p in plan["placement"].items()}


def test_dependencies_come_before_dependants(make_assessed, rules):
    assessed = make_assessed([row("A3", dependencies="A2"), row("A2", dependencies="A1"), row("A1")])
    plan = build_waves(assessed, rules)
    assert wave_of(plan) == {"A1": 1, "A2": 2, "A3": 3}
    assert plan["cycles"] == []


def test_every_dependency_is_in_an_earlier_wave_on_a_larger_graph(make_assessed, rules):
    rows = [row(f"N{i:02d}", dependencies=";".join(f"N{j:02d}" for j in range(i) if (i * 7 + j * 3) % 5 == 0)) for i in range(30)]
    assessed = make_assessed(rows)
    plan = build_waves(assessed, rules)
    w = wave_of(plan)
    for a in assessed:
        for d in a.app.dependencies:
            assert w[d] < w[a.app.app_id]
    assert all(x["size"] <= 8 for x in plan["waves"])


def test_wave_size_limit(make_assessed, rules):
    assessed = make_assessed([row(f"A{i}") for i in range(1, 6)])
    plan = build_waves(assessed, rules, max_wave_size=2)
    assert [w["size"] for w in plan["waves"]] == [2, 2, 1]
    assert [w["apps"] for w in plan["waves"]] == [["A1", "A2"], ["A3", "A4"], ["A5"]]


def test_critical_applications_are_never_in_the_first_wave(make_assessed, rules):
    assessed = make_assessed([row("A1", business_criticality=5), row("A2", business_criticality=2), row("A3", business_criticality=4)])
    plan = build_waves(assessed, rules)
    assert wave_of(plan) == {"A2": 1, "A1": 2, "A3": 2}


def test_wave_one_stays_empty_when_everything_is_critical(make_assessed, rules):
    assessed = make_assessed([row("A1", business_criticality=5), row("A2", business_criticality=4)])
    plan = build_waves(assessed, rules)
    assert plan["waves"][0]["apps"] == []
    assert plan["waves"][1]["apps"] == ["A1", "A2"]
    assert any("Wave 1 has no application" in w for w in plan["warnings"])


def test_refactor_has_an_earliest_wave(make_assessed, rules):
    assessed = make_assessed([
        row("A1", technology="Custom application", change_frequency="high", notes="monolith", business_criticality=2),
        row("A2", business_criticality=2),
    ])
    assert assessed[0].disposition == "refactor"
    assert wave_of(build_waves(assessed, rules)) == {"A2": 1, "A1": 2}


def test_circular_dependencies_are_reported_and_migrate_together(make_assessed, rules):
    assessed = make_assessed([
        row("A1", dependencies="A2"), row("A2", dependencies="A3"), row("A3", dependencies="A1"),
        row("A4", dependencies="A1"),
    ])
    plan = build_waves(assessed, rules)
    assert plan["cycles"] == [{"group": "CYC-1", "apps": ["A1", "A2", "A3"], "example_loop": ["A1", "A2", "A3", "A1"]}]
    w = wave_of(plan)
    assert w["A1"] == w["A2"] == w["A3"] == 1 and w["A4"] == 2
    assert plan["placement"]["A2"]["cycle_group"] == "CYC-1"
    assert any("Circular dependency CYC-1: A1 -> A2 -> A3 -> A1" in x for x in plan["warnings"])


def test_a_cycle_larger_than_the_limit_sits_alone_with_a_warning(make_assessed, rules):
    assessed = make_assessed([row("A1", dependencies="A2"), row("A2", dependencies="A3"), row("A3", dependencies="A1"), row("A4")])
    plan = build_waves(assessed, rules, max_wave_size=2)
    assert any("exceeds the limit" in w for w in plan["warnings"])
    assert plan["waves"][0]["apps"] == ["A4"] or plan["waves"][0]["apps"] == ["A1", "A2", "A3"]
    assert sorted(m for w in plan["waves"] for m in w["apps"]) == ["A1", "A2", "A3", "A4"]


def test_shared_services_are_placed_first(make_assessed, rules):
    assessed = make_assessed([row("A1"), row("A2"), row("Z9", technology="Platform service (DNS)")])
    plan = build_waves(assessed, rules, max_wave_size=1)
    assert [w["apps"] for w in plan["waves"]] == [["Z9"], ["A1"], ["A2"]]
    assert plan["placement"]["Z9"]["shared_service"] is True


def test_an_application_with_many_dependants_counts_as_a_shared_service(make_assessed, rules):
    rows = [row("S1")] + [row(f"D{i}", dependencies="S1") for i in range(3)] + [row("A0")]
    plan = build_waves(make_assessed(rows), rules, max_wave_size=1)
    assert plan["waves"][0]["apps"] == ["S1"]


def test_dependency_in_same_wave_when_allowed(make_assessed):
    rules = load_rules()
    rules["waves"]["allow_dependency_in_same_wave"] = True
    plan = build_waves(make_assessed([row("A2", dependencies="A1"), row("A1")]), rules)
    assert wave_of(plan) == {"A1": 1, "A2": 1}


def test_links_to_applications_outside_the_waves_are_reported(make_assessed, rules):
    assessed = make_assessed([
        row("A1", dependencies="K1;R1;S1"),
        row("K1", vendor_supported_in_cloud="no"),
        row("R1", business_criticality=1, users=0, change_frequency="none"),
        row("S1", technology="SaaS (CRM)"),
        row("K2", vendor_supported_in_cloud="no", dependencies="A1"),
    ])
    plan = build_waves(assessed, rules)
    text = "\n".join(plan["warnings"])
    assert "A1 (wave 1) depends on K1, which stay(s) on premises" in text
    assert "A1 (wave 1) depends on R1, proposed for retirement" in text
    assert "K2 stays on premises but depends on A1 (wave 1)" in text
    assert "S1" not in text
    assert plan["not_scheduled"]["S1"].startswith("not in scope")
    assert plan["not_scheduled"]["K1"] == "retained on premises"


def test_apps_that_are_not_migrating_are_not_scheduled(make_assessed, rules):
    plan = build_waves(make_assessed([row("S1", technology="SaaS")]), rules)
    assert plan["wave_count"] == 0 and any("No application is proposed" in w for w in plan["warnings"])


def test_links_across_the_boundary_after_each_wave(make_assessed, rules):
    plan = build_waves(make_assessed([row("A2", dependencies="A1"), row("A1")]), rules)
    assert [w["cross_boundary_links_after_wave"] for w in plan["waves"]] == [1, 0]


def test_waves_are_independent_of_row_order(make_assessed, rules):
    rows = [row("A3", dependencies="A1;A2"), row("A2", dependencies="A1"), row("A1"), row("A4"), row("A5", business_criticality=5)]
    a = build_waves(make_assessed(rows), rules)
    b = build_waves(make_assessed(list(reversed(rows))), rules)
    assert a == b
    assert a == copy.deepcopy(build_waves(make_assessed(rows), rules))


def test_mermaid_output_names_every_scheduled_app(make_assessed, rules):
    assessed = make_assessed([row("A2", dependencies="A1"), row("A1")])
    text = waves_mermaid(build_waves(assessed, rules), assessed)
    assert text.startswith("flowchart TB") and "n_A1 --> n_A2" in text and 'subgraph W2["Wave 2"]' in text


def test_scc_finds_loops_and_orders_components():
    edges = {"a": ["b"], "b": ["c"], "c": ["a"], "d": ["a"], "e": ["e"]}
    comps = strongly_connected_components(list("abcde"), edges)
    assert comps == [["a", "b", "c"], ["d"], ["e"]]
    assert shortest_cycle_through("a", ["a", "b", "c"], edges) == ["a", "b", "c", "a"]
    assert shortest_cycle_through("d", ["d"], edges) is None


def test_scc_handles_a_very_long_chain_without_recursion_errors():
    n = 5000
    edges = {i: [i + 1] for i in range(n - 1)}
    assert len(strongly_connected_components(range(n), edges)) == n
    edges[n - 1] = [0]
    comps = strongly_connected_components(range(n), edges)
    assert len(comps) == 1 and len(comps[0]) == n
