# Common reasons migrations stall

These are patterns seen repeatedly in migration programmes, with how to spot them early and what to do. They are practitioner observations, not statistics.

| Reason | How it shows | What helps |
|---|---|---|
| **The inventory is wrong or thin** | Surprises appear in wave 3: servers nobody listed, an interface nobody knew of | Run discovery (for example with Azure Migrate) and reconcile it with the inventory before sequencing. Treat the first inventory as a draft |
| **Dependencies are discovered late** | An application moves and a monthly job fails | Capture dependencies from network flows as well as from owners. Group tightly coupled applications. See [wave planning](wave-planning.md) |
| **Vendor support is never confirmed** | A critical application sits in "unknown" for months | Make it a dated task with a named owner and an escalation. Do not plan a critical move on an assumption |
| **The landing zone is built after the plan** | Wave 1 waits for network, identity or policy decisions | Treat the landing zone as wave 0 and gate waves on its [checklist](landing-zone-readiness.md) |
| **Identity is left to last** | Applications that need a directory fail on arrival | Place identity first, and test sign-in from every site |
| **Hybrid link is undersized or untested** | Applications that moved are slow because their database has not | Size from dependency flows, test pairs before each wave, and keep chatty pairs together |
| **Scope creep into modernisation** | "While we are there" refactoring doubles a wave | Move first, modernise second, as separately funded work |
| **The business case assumed savings that do not arrive** | Costs rise after cutover, the sponsor loses faith | Model stranded cost, parallel running and the final-year run rate. See [cost model](cost-model.md) and the [CFO guide](cfo-business-case.md) |
| **Parallel running never ends** | Old and new both cost money for a year | Put a decommission date and an owner on every source |
| **Retained applications become permanent hybrid** | The data centre cannot close because of three applications | List retained applications with a reason and a revisit date. Cost the hybrid link and the stranded data centre |
| **Owners are not engaged** | Test sign-off takes weeks, or is rubber-stamped | Name an owner per application at the start. Agree the test and the window with them |
| **Change freezes and business calendar ignored** | Cutover collides with year end or peak trading | Put the calendar over the wave plan. Plan the next wave in detail, the rest at a high level |
| **Skills are not there** | Operations cannot run what was built | Train before the first production wave. Agree who supports what. Use a partner where the gap is real |
| **Security and compliance arrive as a gate at the end** | A review blocks a finished migration | Involve security at design. Do data protection reviews per wave, early |
| **Licensing surprises** | A vendor says the licence does not allow it, or costs more | Read licences in discovery. Ask vendors in writing before dates are promised |
| **No rollback, or an untested one** | A failed cutover becomes an outage | Rehearse rollback. Use the [template](cutover-and-rollback.md) |
| **Governance is slow or absent** | Every exception waits for a meeting | Agree decision rights, standard designs and pre-approved patterns. See governance items in the checklist |
| **Over-ambitious waves** | Waves slip, then every later wave slips | Size waves by complexity and team capacity, not by application count alone. Add a buffer |
| **Nobody owns the end state** | Migration "completes" with no operating model | Name the owner of cost, security and operations before the first production wave |
| **Sponsor fatigue** | Funding stops after the first hard wave | Report in business terms: risk removed, systems retired, money saved or avoided. Celebrate decommissioning, not just cutovers |

## An early-warning checklist for programme boards

Ask at each wave gate:

1. How many applications are still "unknown" on vendor support, and who owns each?
2. Does every moved application appear in monitoring and backup?
3. What is the actual versus planned duration of the last wave, and have later waves been adjusted?
4. What has been decommissioned, and what is the saving evidenced by an invoice or a contract end?
5. Which retained applications have a revisit date in the next quarter?
6. What is the Azure bill against the estimate, and why does it differ?
