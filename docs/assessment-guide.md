# Assessment guide: questions to ask for each application

The inventory CSV is only as good as the answers behind it. This guide lists the questions that fill each column and the further questions that decide a disposition. Ask the application owner and the technical owner together where you can: the owner knows what the application is for, the technical owner knows what it really connects to.

The structure follows the assessment topics in Microsoft's cloud migration planning guidance (architecture, performance and usage, security and identity, compatibility, dependencies, compliance and operations, code, databases, risk), reordered into the order that works in a workshop. See [sources and verification](sources-and-verification.md).

## 1. What it is and who owns it

| Question | Fills | Why it matters |
|---|---|---|
| What does it do, in one sentence, and which business process stops without it? | `name`, `notes` | A vague purpose usually means a retirement candidate or an unknown dependency |
| Who is the accountable business owner, and who is the technical owner? | `owner` | Someone has to accept the disposition and the cutover window |
| How critical is it, 1 (can be off for a week) to 5 (stops the business within hours)? | `business_criticality` | Critical applications are kept out of the first wave and get more testing effort |
| How many people use it in a normal month, and how many are named users? | `users` | Very low use plus low criticality is the main retirement signal |
| How often does the code or configuration change? none, low, medium, high | `change_frequency` | Frequently changed in-house code is where modernisation pays off. Stable code is best moved as it is |

## 2. Technology and support

| Question | Fills | Why it matters |
|---|---|---|
| Is it packaged software, in-house code, a database, a file service, a shared platform service, or already SaaS? Include one of those words in `technology`. | `technology` | The rules classify the application from this text (see [disposition rules](disposition-rules.md)) |
| Which operating system or platform, and which version? | `os_or_platform` | Mainframe, midrange and some Unix platforms do not run as standard Azure virtual machines |
| When does vendor support end for the operating system, database and the product itself? Use the earliest date. | `end_of_support_date` | An application already out of support should change platform, not just move |
| Does the vendor support this exact version in the cloud, in writing? yes, no, unknown | `vendor_supported_in_cloud` | The single most common cause of a move being stopped late. For in-house code, answer yes if your own team can run it in Azure |
| What is the licence model, and does it restrict where the software can run? | `licence_model` | Hardware-tied, OEM or on-premises-only licences may not transfer. Per-core and per-user terms change the running cost |

## 3. Data and compliance

| Question | Fills | Why it matters |
|---|---|---|
| What is the most sensitive data it holds? low, medium, high, restricted | `data_sensitivity` | Drives the data protection review, region choice and access design |
| Are there contractual, regulatory or customer limits on where the data is stored or who can administer it? | `notes` | Residency and access limits can change the target design |
| What are the recovery time and recovery point objectives, and have they been tested? | `notes` | Sets the backup and disaster recovery design in the landing zone |

## 4. Dependencies

| Question | Fills | Why it matters |
|---|---|---|
| Which other applications must be running for this one to work? List their `app_id` values. | `dependencies` | Input to wave planning. Use the technical owner's view, and check it against network flow data where you have it |
| Which authentication source does it use (directory, single sign-on, local accounts)? | `dependencies` | Identity is almost always a dependency and must be ready first |
| Which interfaces does it have: file feeds, queues, APIs, database links, scheduled jobs? Which are real-time and which are overnight? | `notes` | Overnight feeds can often be treated as loosely coupled. Real-time calls cannot cross a slow link |
| Does it talk to equipment on a site (machine controllers, scanners, label printers, door systems)? | `notes` | Site-bound equipment often needs a low and steady round-trip time. Test before deciding |
| What depends on it? | other rows' `dependencies` | Applications with many dependants are scheduled early and changed cautiously |

## 5. Cost

| Question | Fills | Why it matters |
|---|---|---|
| What does it cost to run per year, all in: hosting share, licences, support, backup, and the part of staff time that is attributable? | `current_annual_cost` | The baseline for the comparison. State your allocation method once and apply it to every row |
| Has Azure Migrate (or equivalent) produced an annual Azure cost estimate for it? | `azure_annual_cost_estimate` (optional column) | Replaces the generic run cost factor for that application |

## 6. Questions to settle before a disposition is accepted

1. Would anyone notice if it were switched off for a month? If not, why is it in the inventory?
2. If the vendor says no or does not reply, what is the plan: replace, keep, or accept the risk in writing?
3. Is there a hard date (end of support, hardware refresh, contract end, site closure) that sets the latest sensible cutover?
4. Who tests it after the move, using what, and what does a pass look like?
5. What is the rollback, and how long does it stay available? See [cutover and rollback](cutover-and-rollback.md).
6. Does the move change anything the users will see (address, sign-in, drive letters, print queues)?

## Common inventory defects to fix before running the tool

- Application names that differ between teams, so one system appears twice. Merge by agreeing one `app_id`.
- Dependencies recorded in one direction only. Ask both owners.
- Costs that mix hosting and support for several applications. Allocate before loading.
- "Unknown" support status left unresolved because the vendor contact has left. Treat as a risk with an owner and a date.
- Servers listed without the application they serve, or applications with no server. Reconcile with discovery output.

The tool reports bad values with line numbers. It cannot tell you that the content is right.
