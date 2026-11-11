# Disposition rules

The `assess` command gives each application a score for each of the six dispositions and picks the highest. Nothing is hidden: every rule that fired is listed in the output with its points, and every score is in `assessment.csv`.

## How the scoring works

1. Each application starts with the **baseline** points (rehost 2, the others 0), which makes a plain, supported application default to the lowest-change route.
2. Each rule has a condition. If it matches, its points are added (or subtracted) for the dispositions it names, and its plain-English reason is recorded.
3. A rule can also **decide** the disposition outright. Only one does by default: an application already delivered as SaaS is retained and left out of scope.
4. The highest score wins. A tie is broken by `tie_break_order` (rehost, replatform, retain, repurchase, refactor, retire) and is always flagged and sent for review.
5. **Confidence** comes from the margin between the winner and the runner-up: high at 4 points or more, medium at 2 or 3, low below that. These thresholds are settings.
6. An application **needs review** when confidence is low, when there was a tie, or when a rule marked "review" shaped the result (unknown vendor support, a retirement, a platform that cannot run as a standard virtual machine).
7. Next steps and flags are attached only when they matter for the chosen disposition. A retirement candidate is not told to ask the vendor about cloud support.

The scores are a way of making judgement visible and repeatable. They are not measurements, and a margin of one point is a close call.

## Derived fields

| Field | Meaning |
|---|---|
| `tech_class` | `saas`, `platform_service`, `file_service`, `custom`, `package`, `database` or `other`, from keywords in `technology` (table below) |
| `eos_status` | `past` (end of support on or before the as-of date), `soon` (within `eos_soon_months`, default 12), `later`, or `none` (no date) |
| `dependents_count` | How many other applications list this one as a dependency |
| `text`, `platform_text` | Lower-case text used for keyword matching: notes plus technology, and operating system plus technology |

Give `--as-of` a date to make results reproducible. Without one, today's date is used and the tool says so.

## The default rules

This table is generated from [`migration_planner/default_rules.json`](../migration_planner/default_rules.json) by `tools/build_docs.py`, and a test fails if it is out of date.

<!-- rules-table:start -->

| ID | Rule | When | Points | Reason given in the output |
|---|---|---|---|---|
| R01 | already_saas | `tech_class` = saas | decides: retain (out of scope) | Already delivered as SaaS, so there is nothing to migrate. It is left out of the waves and out of the cost comparison. Check that its integrations still work after the apps around it move. |
| R02 | platform_not_available_as_standard_vm | `platform_text` mentions any of `@blocked_platform_keywords` | rehost -5, replatform -4, refactor +1, repurchase +2, retain +5 | The platform is one that does not run as a standard Azure virtual machine, so a like-for-like move is unlikely to be possible. Replacement or a specialist hosting partner are the realistic routes; confirm against current Azure documentation. |
| R03 | latency_or_local_hardware | `text` mentions any of `@latency_or_hardware_keywords` | rehost -1, retain +4 | The description points to equipment or response times tied to a physical site (machine control, scanners, label printing or similar). These are usually kept near the site, or moved only after a network and latency test. |
| R04 | vendor_does_not_support_cloud | `vendor_supported_in_cloud` = no | rehost -3, replatform -3, refactor +1, repurchase +3, retain +3 | The vendor does not support this application in the cloud. Running it there anyway risks losing vendor support, so the choices are to keep it, replace it, or rebuild it. |
| R05 | vendor_support_unknown | `vendor_supported_in_cloud` = unknown | rehost -1, replatform -1, retain +1 | Vendor support in the cloud has not been confirmed. The score is held back until it is, because moving an application on an assumption is how migrations fail. |
| R06 | critical_and_support_unknown | `vendor_supported_in_cloud` = unknown and `business_criticality` >= 4 | retain +2 | Business criticality is {business_criticality} and vendor support is unconfirmed. A critical application should not move on an assumption. |
| R07 | vendor_supports_cloud | `vendor_supported_in_cloud` = yes | rehost +1, replatform +1 | Supported in the cloud, which keeps the lower-change routes open. |
| R08 | support_has_ended | `eos_status` = past | replatform +3, refactor +1, repurchase +2, retire +1, retain -2 | Support for the operating system or product ended on {end_of_support_date}. Staying as it is is not a durable answer. Moving the machine unchanged only changes where the risk sits, so the platform should change or the application should be replaced or retired. |
| R09 | support_ends_soon | `eos_status` = soon | replatform +1, repurchase +1 | Support ends on {end_of_support_date}, within the next {eos_soon_months} months. Plan the remediation as part of the move rather than after it. |
| R10 | low_use_low_criticality | `users` <= 3 and `business_criticality` <= 2 | retire +5 | Only {users} user(s) and business criticality {business_criticality}. Low use and low criticality make this a retirement candidate. |
| R11 | notes_suggest_retirement | `notes` mentions any of `@retire_note_keywords` | retire +4 | The notes suggest the application is duplicated, superseded or no longer used. |
| R12 | unchanged_and_little_used | `change_frequency` = none and `users` <= 20 and `business_criticality` <= 2 | retire +2 | Nobody changes it, few people use it and it is not critical. |
| R13 | high_criticality_favours_low_change | `business_criticality` >= 4 | rehost +1, refactor -2, repurchase -1, retire -4 | Business criticality is {business_criticality}. A critical application favours the route with the least change, and it is not a retirement candidate. |
| R14 | refactor_needs_own_code | `tech_class` is not custom | refactor -4 | Refactoring needs source code the organisation controls. This is not recorded as in-house custom code. |
| R15 | vendor_offers_saas | `notes` mentions any of `@repurchase_note_keywords` | repurchase +4 | The notes say a SaaS or hosted version of the product exists, which makes repurchase a real option. |
| R16 | custom_and_actively_changed | `tech_class` = custom and `change_frequency` = high | replatform +3, refactor +2 | In-house code that changes often gains from modernisation, and the team is already working in it. Moving to a managed platform is the usual first step. |
| R17 | custom_and_stable | `tech_class` = custom and `change_frequency` is one of low, none | rehost +1, refactor -2 | Stable in-house code rarely repays the cost of refactoring. Move it first and revisit once it is running in Azure. |
| R18 | database_to_managed_service | `tech_class` = database | replatform +3 | A database often benefits from a managed service, which removes patching and backup work. Check engine version and feature compatibility first. |
| R19 | file_service_to_managed_service | `tech_class` = file_service | replatform +3 | File services usually move to a managed file or collaboration service rather than a like-for-like virtual machine. Check permissions, long paths and applications that use drive letters. |
| R20 | shared_platform_service | `tech_class` = platform_service | replatform +2 | A shared platform service. These usually move to the cloud equivalent, and the landing zone design depends on them, so they are scheduled early. |
| R21 | sensitive_data | `data_sensitivity` is one of high, restricted | retain +1 | Data sensitivity is {data_sensitivity}. That does not stop a move, but it needs a data protection review, region and residency checks and tighter access design first. |
| R22 | restrictive_licence | `licence_model` mentions any of `@restrictive_licence_keywords` | rehost -2, replatform -2, repurchase +1, retain +2 | The licence terms ({licence_model}) may not allow the software to run on shared cloud hosts. |
| R23 | many_dependants | `dependents_count` >= 5 | refactor -1, repurchase -1 | {dependents_count} other applications depend on it, so a change in behaviour ripples out. Prefer a route that keeps interfaces the same. |
| R24 | notes_point_to_architecture_limits | `tech_class` = custom and `notes` mentions any of `@refactor_note_keywords` | refactor +4 | The notes describe limits in how the in-house application is built (for example scaling or accumulated technical debt), which is what refactoring addresses. |

Baseline points before any rule: rehost 2.

Keyword lists used by the rules (whole words, case-insensitive, a plural ending is accepted):

- `blocked_platform_keywords`: mainframe, as/400, as400, ibm i, hp-ux, solaris, openvms, tru64, aix
- `latency_or_hardware_keywords`: plc, scada, shop floor, shop-floor, production line, radio frequency, serial port, label printer
- `retire_note_keywords`: decommission, duplicate, superseded, replaced by, no longer used, redundant, unused
- `repurchase_note_keywords`: saas version, vendor saas, saas equivalent, vendor offers saas, hosted version
- `refactor_note_keywords`: monolith, does not scale, cannot scale, struggles at peak, re-architect, rearchitect, rewrite, technical debt
- `restrictive_licence_keywords`: oem, hardware-locked, hardware locked, dongle, cpu-locked, on-premises only, on premises only

Technology classes, matched in this order against `technology` (first match wins; anything else is `other`):

- `saas`: saas, software as a service, vendor hosted, vendor-hosted, microsoft 365
- `platform_service`: platform service, directory service, active directory, dns, dhcp, certificate, print server, monitoring, backup, sftp, edi gateway, smtp, message broker
- `file_service`: file service, file server, file share, nas
- `custom`: custom, bespoke, in-house, inhouse
- `package`: package, packaged, cots, commercial, erp
- `database`: database, sql server, oracle, postgres, mysql, data warehouse

<!-- rules-table:end -->

## Changing the rules

Print the defaults, edit a copy, and pass it back:

```bash
python -m migration_planner show-rules > rules.json
python -m migration_planner assess inventory.csv --rules rules.json --as-of 2026-11-11
```

What you can change in the file:

- **Points** on any rule, the **baseline**, the **tie-break order**, the confidence margins and the end-of-support horizon.
- **Keyword lists** under `keywords` and the **technology classes**. Replace the words with the vocabulary your organisation uses.
- **Add a rule**: give it an `id`, a `when` condition, `points` (or `force`), a plain-English `reason`, and optionally `flag`, `action`, `review` and `ignore_for_dispositions`.
- **Wave settings** under `waves` (see [wave planning](wave-planning.md)).

A condition is `{"field": ..., "op": ..., "value": ...}`, or `{"all": [...]}` / `{"any": [...]}` of conditions. Operators: `eq`, `ne`, `in`, `not_in`, `lt`, `lte`, `gt`, `gte`, `contains_any` (a list of words, or `@name` for a keyword list), `is_blank`, `not_blank`. Reasons can use `{field}` placeholders such as `{users}` or `{end_of_support_date}`.

A section you supply replaces the default section completely, so copy the whole section before editing it. Bad rules stop the run with a message naming the rule and the problem.

## Human decisions override the rules

The rules propose. People decide. Record decisions in a CSV with `app_id`, `disposition` and a required `reason`, and pass it with `--overrides`:

```bash
python -m migration_planner plan inventory.csv --assumptions cost.json --overrides decisions.csv --as-of 2026-11-11
```

An overridden application keeps the rules' proposal in its reason list ("Human decision: retain. Rules proposed rehost. Reason given: ..."), so the audit trail shows both. See [`examples/overrides.example.csv`](../examples/overrides.example.csv).

## What the rules cannot know

- Whether the data in the inventory is true.
- Anything not in the columns: contract terms, political history, a vendor's mood.
- How an application behaves under load, or what really talks to it. That is what discovery and assessment tooling is for.

Use the output to start the conversation with each owner, not to end it.
