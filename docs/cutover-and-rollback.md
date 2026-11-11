# Cutover and rollback template

Use one copy per application or per wave. Fill every field before the go or no-go meeting. A blank field is an unanswered question, not a formality. Guidance from Microsoft on migration planning says the same about the essentials: define failure criteria, agree who can call a rollback, test the rollback, and get stakeholder approval in writing.

## 1. Scope

| Field | Entry |
|---|---|
| Wave and applications | |
| Disposition for each (rehost, replatform, refactor, repurchase) | |
| Business owner and technical owner | |
| Cutover window (start, end), and why this window | |
| Periods avoided (financial close, peak trading, audits, holidays) | |
| Downtime approach: planned outage, or near-zero downtime with continuous replication | |
| Dependencies that must already be in place (landing zone items, upstream applications) | |
| Dependants that must be told | |

## 2. Entry criteria (all must be true to start)

- [ ] Landing zone checklist items for this wave are done, with evidence ([checklist](landing-zone-readiness.md))
- [ ] Vendor support in the cloud confirmed in writing, or the risk accepted in writing by the owner
- [ ] Test migration completed at least once, with timings recorded
- [ ] Restore from the new backups tested and timed
- [ ] Hybrid link tested for latency and bandwidth for the pairs that straddle the boundary
- [ ] Monitoring and alerting live on the target, routed to named people
- [ ] Users, helpdesk and dependants notified, with what will change for them
- [ ] Test plan and test users named and available
- [ ] Rollback tested in a rehearsal, not just written down
- [ ] Decision-maker and deputy reachable throughout the window

## 3. Runbook

| Step | Owner | Planned start | Duration | Done (time and initials) | Notes |
|---|---|---|---|---|---|
| Freeze changes on the source | | | | | |
| Final backup of the source, verified | | | | | |
| Stop the application, or stop writes | | | | | |
| Final data sync | | | | | |
| Start the target | | | | | |
| Repoint names, addresses and integrations | | | | | |
| Smoke tests (see section 4) | | | | | |
| Go or no-go checkpoint (see section 5) | | | | | |
| Open to users | | | | | |
| Enhanced monitoring period begins | | | | | |

## 4. Acceptance tests

| Test | Expected result | Run by | Pass or fail |
|---|---|---|---|
| Sign-in with a normal user and an administrator | | | |
| A complete business transaction end to end | | | |
| Each inbound and outbound interface | | | |
| Reports and scheduled jobs | | | |
| Printing, scanning or equipment connections | | | |
| Performance against the agreed baseline | | | |
| Backup runs and a test restore | | | |
| Monitoring alert fires and reaches the right person | | | |

## 5. Failure criteria and go or no-go checkpoints

Agree these before the window, in numbers where possible.

| Criterion | Threshold | Checked at |
|---|---|---|
| Any acceptance test in section 4 fails | Any failure on a critical test is a stop | Checkpoint 1 |
| Error rate or response time | Worse than the agreed baseline by more than ... | Checkpoint 1 and after 1 hour |
| Data reconciliation | Differences above ... records | Before opening to users |
| Time | Not at checkpoint 1 by ... (rollback needs ... to complete) | Clock time |

**Who can call a rollback:** (named person and deputy). **Who must be told:** (list).

Decide the latest point of no return in advance, and write it down.

## 6. Rollback

| Field | Entry |
|---|---|
| Trigger (reference section 5) | |
| What "back" means (source restarted, names repointed, data resynchronised) | |
| Data written to the target since cutover: how it returns to the source, or is accepted as lost | |
| Steps, owner and duration for each | |
| Maximum time rollback needs | |
| How long the source stays intact and available (days) | |
| Who confirms rollback complete | |
| Communication: what users and dependants are told | |

The source is not decommissioned until the rollback window has closed and the owner has signed off. Keep the old backups as well.

## 7. After cutover

- [ ] Enhanced monitoring for a defined period, with a named watcher
- [ ] Parallel running reviewed daily, then ended on a date
- [ ] Defects and user reports triaged in one list
- [ ] Cost checked against the estimate after the first full billing period
- [ ] Source decommissioned on an agreed date, with evidence (and the saving recorded)
- [ ] Lessons recorded and fed into the next wave

## 8. Sign-off

| Role | Name | Decision | Date and time |
|---|---|---|---|
| Business owner | | | |
| Technical owner | | | |
| Migration lead | | | |
| Security | | | |
