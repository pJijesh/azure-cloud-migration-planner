"""Build migration waves from the dependency graph.

Method, in order:

1. Only applications that move or are replaced (rehost, replatform, refactor, repurchase) are
   scheduled. Retained, retired and already-SaaS applications are not in the waves, but links to
   them are reported.
2. Circular dependencies are found (strongly connected components) and each loop is treated as one
   unit that migrates in a single wave. Every loop is reported, with one concrete path.
3. Units are ordered so that, by default, a unit's dependencies are in an earlier wave.
4. Within the limits, shared services (platform services, or applications with many dependants)
   are placed first, then the chains with the longest tail of dependants, then lower criticality.
5. Constraints: a wave size limit (in applications), a critical application is never in the first
   wave, and some dispositions have an earliest wave.
"""

from __future__ import annotations

from collections import Counter

from .graph import shortest_cycle_through, strongly_connected_components
from .model import DISPOSITIONS, MIGRATING


def _edges(assessed):
    return {a.app.app_id: list(a.app.dependencies) for a in assessed}


def build_waves(assessed, rules, max_wave_size=None):
    cfg = dict(rules["waves"])
    if max_wave_size is not None:
        if max_wave_size < 1:
            raise ValueError("max_wave_size must be 1 or more")
        cfg["max_wave_size"] = max_wave_size
    limit = cfg["max_wave_size"]
    by_id = {a.app.app_id: a for a in assessed}
    edges = _edges(assessed)
    migrating = sorted(i for i, a in by_id.items() if a.disposition in MIGRATING and a.in_scope)
    warnings: list[str] = []

    sccs = strongly_connected_components(migrating, edges)
    unit_of = {}
    units = []
    cycles = []
    for comp in sccs:
        idx = len(units)
        is_cycle = len(comp) > 1
        group = ""
        if is_cycle:
            group = f"CYC-{len(cycles) + 1}"
            path = shortest_cycle_through(comp[0], comp, edges)
            cycles.append({"group": group, "apps": comp, "example_loop": path})
            warnings.append(
                f"Circular dependency {group}: {' -> '.join(path)}. These {len(comp)} applications are "
                f"scheduled together in one wave and must be cut over together. Check whether every link "
                f"is a real runtime dependency: a reporting feed or file extract can often be treated as "
                f"loosely coupled, which would let them move separately."
            )
        crit = max(by_id[m].app.business_criticality for m in comp)
        min_wave = 1
        if crit >= cfg["critical_min_criticality"]:
            min_wave = max(min_wave, cfg["critical_min_wave"])
        for m in comp:
            min_wave = max(min_wave, cfg["min_wave_by_disposition"].get(by_id[m].disposition, 1))
        shared = any(
            by_id[m].tech_class in cfg["shared_service_classes"]
            or by_id[m].dependents_count >= cfg["shared_service_min_dependents"]
            for m in comp
        )
        units.append(
            {
                "members": comp,
                "group": group,
                "crit": crit,
                "min_wave": min_wave,
                "shared": shared,
                "deps": set(),
                "dependents": set(),
            }
        )
        for m in comp:
            unit_of[m] = idx
    for idx, u in enumerate(units):
        for m in u["members"]:
            for d in edges[m]:
                if d in unit_of and unit_of[d] != idx:
                    u["deps"].add(unit_of[d])
                    units[unit_of[d]]["dependents"].add(idx)

    # Longest chain of dependants above each unit (depth), computed from a dependency-first order.
    indeg = {i: len(u["deps"]) for i, u in enumerate(units)}
    ready = sorted(i for i, n in indeg.items() if n == 0)
    topo = []
    while ready:
        i = ready.pop(0)
        topo.append(i)
        for j in sorted(units[i]["dependents"]):
            indeg[j] -= 1
            if indeg[j] == 0:
                ready.append(j)
                ready.sort()
    assert len(topo) == len(units), "internal error: cycle left after condensation"
    for i in reversed(topo):
        u = units[i]
        u["depth"] = max((units[j]["depth"] + 1 for j in u["dependents"]), default=0)
        u["key"] = (0 if u["shared"] else 1, -u["depth"], u["crit"], u["members"][0])

    order = sorted(range(len(units)), key=lambda i: units[i]["key"])
    placed: dict[int, int] = {}
    wave_units: list[list[int]] = []
    same_wave = cfg["allow_dependency_in_same_wave"]
    wave_no, guard = 1, 0
    while len(placed) < len(units):
        guard += 1
        if guard > len(units) + 50:
            raise RuntimeError("internal error: wave placement did not finish")
        current: list[int] = []
        size = 0
        while True:
            chosen = None
            for i in order:
                if i in placed:
                    continue
                u = units[i]
                if u["min_wave"] > wave_no:
                    continue
                ok = all((d in placed and (placed[d] < wave_no or (same_wave and placed[d] == wave_no))) for d in u["deps"])
                if not ok:
                    continue
                if size > 0 and size + len(u["members"]) > limit:
                    continue
                chosen = i
                break
            if chosen is None:
                break
            placed[chosen] = wave_no
            current.append(chosen)
            size += len(units[chosen]["members"])
        wave_units.append(current)
        wave_no += 1

    placement = {}
    for k, us in enumerate(wave_units, start=1):
        for i in us:
            for m in units[i]["members"]:
                placement[m] = {"wave": k, "cycle_group": units[i]["group"], "shared_service": units[i]["shared"]}
            if len(units[i]["members"]) > limit:
                warnings.append(
                    f"Cycle group {units[i]['group']} has {len(units[i]['members'])} applications, more than the "
                    f"wave size limit of {limit}. It sits alone in wave {k} and exceeds the limit."
                )

    if wave_units and not wave_units[0]:
        warnings.append(
            "Wave 1 has no application. Every candidate is critical, has a later earliest wave, or depends "
            "on a critical application. Use wave 1 to prove the landing zone with a pilot workload that is not "
            "in this inventory."
        )
    if not migrating:
        warnings.append("No application is proposed for migration, so there are no waves.")

    # Links to applications that are not in the waves, grouped so each application is named once.
    for a_id in migrating:
        to_retained = [d for d in edges[a_id] if by_id[d].disposition == "retain" and by_id[d].in_scope]
        to_retired = [d for d in edges[a_id] if by_id[d].disposition == "retire"]
        if to_retained:
            warnings.append(
                f"{a_id} (wave {placement[a_id]['wave']}) depends on {', '.join(to_retained)}, which stay(s) on premises. "
                f"The link must work across the hybrid connection permanently: test latency and bandwidth."
            )
        if to_retired:
            warnings.append(
                f"{a_id} (wave {placement[a_id]['wave']}) depends on {', '.join(to_retired)}, proposed for retirement. "
                f"Remove or replace the dependency before it is switched off."
            )
    for d_id, d in sorted(by_id.items()):
        if d.disposition == "retain" and d.in_scope:
            moving = [f"{dep} (wave {placement[dep]['wave']})" for dep in edges[d_id] if dep in placement]
            if moving:
                warnings.append(
                    f"{d_id} stays on premises but depends on {', '.join(moving)}. Once those move it calls into Azure "
                    f"across the hybrid connection: test latency and bandwidth."
                )
    for d_id, d in sorted(by_id.items()):
        if d.disposition == "retire":
            users_of = sorted(i for i, a in by_id.items() if d_id in a.app.dependencies and a.disposition != "retire")
            if users_of:
                warnings.append(
                    f"{d_id} is proposed for retirement but {', '.join(users_of)} still depend on it. "
                    f"Do not retire it until those links are removed."
                )

    # Network links that cross the on premises and Azure boundary after each wave.
    in_scope_onprem = {
        i for i, a in by_id.items() if a.in_scope and a.disposition != "retire"
    }
    boundary = []
    for k in range(1, len(wave_units) + 1):
        azure = {m for m, p in placement.items() if p["wave"] <= k}
        links = 0
        for a_id in in_scope_onprem:
            for d in edges[a_id]:
                if d in in_scope_onprem and ((a_id in azure) != (d in azure)):
                    links += 1
        boundary.append(links)

    waves = []
    for k, us in enumerate(wave_units, start=1):
        members = sorted(m for i in us for m in units[i]["members"])
        counts = Counter(by_id[m].disposition for m in members)
        waves.append(
            {
                "wave": k,
                "size": len(members),
                "apps": members,
                "by_disposition": {d: counts[d] for d in DISPOSITIONS if counts[d]},
                "max_criticality": max((by_id[m].app.business_criticality for m in members), default=0),
                "shared_services": sorted(m for m in members if placement[m]["shared_service"]),
                "cycle_groups": sorted({placement[m]["cycle_group"] for m in members if placement[m]["cycle_group"]}),
                "cross_boundary_links_after_wave": boundary[k - 1],
            }
        )

    not_scheduled = {}
    for i, a in sorted(by_id.items()):
        if i in placement:
            continue
        if not a.in_scope:
            not_scheduled[i] = "not in scope (already SaaS or otherwise unchanged)"
        elif a.disposition == "retain":
            not_scheduled[i] = "retained on premises"
        elif a.disposition == "retire":
            not_scheduled[i] = "retire (decommission task, not a migration)"
    return {
        "settings": {
            "max_wave_size": limit,
            "critical_min_criticality": cfg["critical_min_criticality"],
            "critical_min_wave": cfg["critical_min_wave"],
            "shared_service_min_dependents": cfg["shared_service_min_dependents"],
            "shared_service_classes": list(cfg["shared_service_classes"]),
            "min_wave_by_disposition": dict(sorted(cfg["min_wave_by_disposition"].items())),
            "allow_dependency_in_same_wave": same_wave,
        },
        "wave_count": len(waves),
        "waves": waves,
        "placement": {m: placement[m] for m in sorted(placement)},
        "cycles": cycles,
        "not_scheduled": not_scheduled,
        "warnings": warnings,
    }


def waves_mermaid(plan, assessed) -> str:
    """A Mermaid flowchart: one box per wave, arrows from each dependency to the application that needs it."""
    by_id = {a.app.app_id: a for a in assessed}
    lines = ["flowchart TB", "  %% An arrow runs from a dependency to the application that needs it, so it points to a later wave."]
    for w in plan["waves"]:
        lines.append(f'  subgraph W{w["wave"]}["Wave {w["wave"]}"]')
        lines.append("    direction LR")
        for m in w["apps"]:
            name = by_id[m].app.name.replace('"', "'")
            lines.append(f'    {_node(m)}["{m}<br/>{name}<br/>{by_id[m].disposition}"]')
        lines.append("  end")
    hub_min = plan["settings"]["shared_service_min_dependents"] * 3
    hidden = 0
    for m in plan["placement"]:
        for d in by_id[m].app.dependencies:
            if d not in plan["placement"]:
                continue
            if by_id[d].dependents_count >= hub_min:
                hidden += 1  # a hub that nearly everything uses would hide the structure
                continue
            lines.append(f"  {_node(d)} --> {_node(m)}")
    if hidden:
        lines.append(f"  %% {hidden} link(s) to widely used shared services are not drawn")
    cyc = [_node(m) for c in plan["cycles"] for m in c["apps"]]
    shared = [_node(m) for m, p in plan["placement"].items() if p["shared_service"] and not p["cycle_group"]]
    lines.append("  classDef cycle fill:#fde2e2,stroke:#b42318,color:#111")
    lines.append("  classDef shared fill:#e0ecff,stroke:#1d4ed8,color:#111")
    if cyc:
        lines.append(f"  class {','.join(cyc)} cycle")
    if shared:
        lines.append(f"  class {','.join(shared)} shared")
    return "\n".join(lines) + "\n"


def _node(app_id: str) -> str:
    return "n_" + "".join(c if c.isalnum() else "_" for c in app_id)
