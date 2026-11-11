# Landing zone readiness checklist

<!-- Generated from landing-zone-readiness.csv by tools/build_docs.py. Edit the CSV, not this file. -->

A landing zone is the prepared Azure environment that workloads move into: tenant and billing, subscriptions, identity, network, security, monitoring, backup, governance and cost controls. Microsoft's Azure landing zone guidance groups the design work into design areas, shown in the second column of the CSV. This checklist is organised by the topics a migration programme has to answer, and each item says which wave it has to be done before.

How to use it: copy [landing-zone-readiness.csv](landing-zone-readiness.csv), fill `owner`, `status` (not started, in progress, done, not applicable) and `notes`, and review it at each wave gate. An item marked done needs the evidence named beside it.

Timing values: **pilot wave** (before the first workload moves), **first production wave**, **each wave** (repeat for every wave), **programme end**.

It is a starting list, not an exhaustive design. Compare it with Microsoft's current landing zone guidance and with your own security and regulatory requirements. See [sources and verification](sources-and-verification.md).

## Billing and tenant

Who pays, and which directory the estate belongs to.

- [ ] **BIL-01** The agreement type and billing account are confirmed, with at least two named billing owners. *Needed before: pilot wave.* Why: Billing set up late or by one person blocks subscriptions and invoices. Evidence: Billing account screenshot or export, owner list.
- [ ] **BIL-02** The decision to reuse the existing Microsoft Entra tenant or create a new one is recorded with the reasons. *Needed before: pilot wave.* Why: A second tenant is hard to merge later and splits identity and licensing. Evidence: Decision record.
- [ ] **BIL-03** At least two people hold the highest tenant and billing roles, and the roles are reviewed. *Needed before: pilot wave.* Why: One person leaving or being unavailable must not lock the organisation out. Evidence: Role assignment list, review date.
- [ ] **BIL-04** Invoice routing, purchase order handling and cost centre mapping are agreed with finance. *Needed before: first production wave.* Why: Invoices that nobody recognises or can code get disputed or paid late. Evidence: Finance sign-off.

## Resource organisation

Management groups, subscriptions, naming, tags and regions.

- [ ] **RES-01** The management group hierarchy is designed and documented (platform, workload landing zones, sandbox, decommissioned). *Needed before: pilot wave.* Why: The hierarchy is where policy and access are inherited. Redesigning it later moves everything. Evidence: Diagram and decision record.
- [ ] **RES-02** The subscription design is agreed (for example one per workload environment or per team) and service limits were checked. *Needed before: pilot wave.* Why: Subscriptions are the unit of scale, billing and isolation. Evidence: Design note, quota check.
- [ ] **RES-03** A naming standard and a required tag set (owner, cost centre, environment, criticality, data classification) are published. *Needed before: pilot wave.* Why: Without tags, cost and ownership questions cannot be answered later. Evidence: Standard document.
- [ ] **RES-04** Primary and secondary regions are chosen with data residency and latency in mind. *Needed before: pilot wave.* Why: Region is hard to change once data and dependencies are in place. Evidence: Decision record, residency review.

## Identity

How people and workloads sign in and what they may do.

- [ ] **IDN-01** The identity source of truth is decided and synchronisation from the on premises directory to Microsoft Entra ID works. *Needed before: pilot wave.* Why: Identity is the main security boundary in the cloud and every other design depends on it. Evidence: Sync health report, test sign-in.
- [ ] **IDN-02** Multifactor authentication is enforced for all administrators, and baseline Conditional Access policies are in place. *Needed before: pilot wave.* Why: Administrator accounts are the most valuable target. Evidence: Policy export, test results.
- [ ] **IDN-03** Privileged access is role based with just-in-time elevation (for example Privileged Identity Management), no standing owner rights, and scheduled access reviews. *Needed before: first production wave.* Why: Standing high privilege turns one stolen credential into a full breach. Evidence: Role report, review schedule.
- [ ] **IDN-04** Emergency access accounts exist, are excluded from policies that could lock them out, are monitored, and were tested. *Needed before: pilot wave.* Why: A policy mistake must not lock everyone out of the tenant. Evidence: Test record, alert on use.
- [ ] **IDN-05** Workloads use managed identities or service principals with a named owner, and no shared administrator passwords exist. *Needed before: first production wave.* Why: Shared credentials cannot be traced or rotated safely. Evidence: Inventory of workload identities.
- [ ] **IDN-06** Role assignments are made to groups, not individuals, with named group owners. *Needed before: first production wave.* Why: Individual assignments are never cleaned up. Evidence: Group and role report.
- [ ] **IDN-07** Where lifted applications need domain join, domain controllers or an equivalent service are available in Azure and tested. *Needed before: first production wave.* Why: Many legacy applications fail without a reachable directory. Evidence: Join test, replication health.

## Network

Addressing, connectivity, name resolution, filtering and segmentation.

- [ ] **NET-01** The IP address plan is agreed, does not overlap with on premises, partner or other cloud networks, and leaves room to grow. *Needed before: pilot wave.* Why: Overlap blocks connectivity and re-addressing is painful. Evidence: Address plan, overlap check.
- [ ] **NET-02** The topology (for example hub and spoke, or Virtual WAN) is chosen and the reasons are recorded. *Needed before: pilot wave.* Why: Topology determines routing, inspection and cost. Evidence: Design note.
- [ ] **NET-03** Hybrid connectivity (private circuit and or VPN) is in place with a resilient path, and bandwidth was sized from the dependency flows. *Needed before: pilot wave.* Why: Every wave leaves some links crossing between on premises and Azure. Evidence: Circuit order, throughput test, failover test.
- [ ] **NET-04** Name resolution works in both directions between on premises and Azure, including private zones. *Needed before: pilot wave.* Why: Broken DNS is the most common cause of a failed cutover. Evidence: Resolution test results.
- [ ] **NET-05** Central filtering (firewall or network virtual appliance), internet egress and ingress rules are designed and reviewed. *Needed before: first production wave.* Why: Traffic leaving or entering the estate needs one controlled path. Evidence: Rule review.
- [ ] **NET-06** Segmentation (network security groups, separation by environment and data sensitivity) is designed and tested. *Needed before: first production wave.* Why: Flat networks let a single compromise spread. Evidence: Design note, test results.
- [ ] **NET-07** Latency and bandwidth were measured for every pair of applications that will straddle the boundary between waves. *Needed before: each wave.* Why: A call that took 1 ms on one network can take far longer across a link. Evidence: Test results by application pair.
- [ ] **NET-08** Administrator and user remote access avoids public management ports. *Needed before: first production wave.* Why: Exposed management ports are attacked within hours. Evidence: Port scan, access design.

## Security

Baseline, posture management, keys, logging and incident response.

- [ ] **SEC-01** A security baseline for Azure is approved, with named owners for approving and monitoring it. *Needed before: pilot wave.* Why: Standards without owners decay. Evidence: Approved baseline.
- [ ] **SEC-02** Cloud security posture management (for example Microsoft Defender for Cloud) is enabled for all subscriptions and recommendations are triaged. *Needed before: pilot wave.* Why: Misconfiguration is the common cause of cloud breaches. Evidence: Coverage report, triage log.
- [ ] **SEC-03** Encryption at rest and in transit defaults are set, and the approach to keys (for example Azure Key Vault, customer managed keys or not) is decided. *Needed before: first production wave.* Why: Key decisions are expensive to reverse. Evidence: Decision record.
- [ ] **SEC-04** Endpoint protection and vulnerability scanning cover migrated virtual machines. *Needed before: each wave.* Why: Migrated machines often arrive with old agents or none. Evidence: Coverage report.
- [ ] **SEC-05** Security logs flow to a central workspace and the security team's tooling, with retention agreed. *Needed before: first production wave.* Why: Logs not collected from day one cannot be recovered after an incident. Evidence: Log source list, retention setting.
- [ ] **SEC-06** The incident response plan covers Azure resources: who acts, how to isolate a workload, and how to contact the provider. *Needed before: first production wave.* Why: A plan written for on premises does not say how to isolate a cloud workload. Evidence: Updated plan, exercise record.
- [ ] **SEC-07** A data protection review is complete for applications holding high or restricted data, with region and residency recorded. *Needed before: each wave.* Why: Moving personal or regulated data without a review can breach obligations. Evidence: Review record.
- [ ] **SEC-08** Third party access (vendors, managed service providers) has a defined route, role and expiry. *Needed before: first production wave.* Why: Standing supplier access is a common weak point. Evidence: Access design, list of third party accounts.

## Governance

Policy, standards, decision rights and guard rails.

- [ ] **GOV-01** Baseline Azure Policy assignments exist (allowed regions, required tags, approved sizes, no public addresses on machines unless approved). *Needed before: pilot wave.* Why: Policy enforces the standards without relying on people remembering. Evidence: Policy list, compliance report.
- [ ] **GOV-02** Policy compliance is reviewed regularly and exemptions have an owner and an expiry date. *Needed before: first production wave.* Why: Permanent exceptions become the standard. Evidence: Review log, exemption register.
- [ ] **GOV-03** Infrastructure as code is the default route for deployment, and portal changes to production are restricted. *Needed before: first production wave.* Why: Hand-built environments cannot be reproduced or audited. Evidence: Pipeline, access list.
- [ ] **GOV-04** Decision rights and change process are defined: who approves new subscriptions, networks and exceptions. *Needed before: pilot wave.* Why: Without them the design drifts through urgent requests. Evidence: Process document.
- [ ] **GOV-05** Resource locks or deletion protection are applied to critical shared resources. *Needed before: first production wave.* Why: Accidental deletion of a shared service takes down many applications. Evidence: Lock list.

## Monitoring

Visibility, alerting and patching.

- [ ] **MON-01** A central log workspace is designed and platform logs (such as activity logs) are collected. *Needed before: pilot wave.* Why: Operations and security need one place to look. Evidence: Workspace design, log source list.
- [ ] **MON-02** Monitoring agents or data collection are on migrated machines, with baseline alerts (availability, CPU, memory, disk). *Needed before: each wave.* Why: Machines that moved silently stop being watched if this is skipped. Evidence: Coverage report, alert list.
- [ ] **MON-03** Alerts route to named on-call people with agreed severity and response times, and routing was tested. *Needed before: first production wave.* Why: An alert nobody receives is not monitoring. Evidence: Test alert record.
- [ ] **MON-04** Service health and resource health notifications reach the operations team. *Needed before: first production wave.* Why: Provider-side problems must not be discovered from user complaints. Evidence: Notification configuration.
- [ ] **MON-05** Patching and configuration drift management is defined: who patches, when, and how it is verified. *Needed before: each wave.* Why: Moved machines are often out of the patching routine. Evidence: Patch schedule, compliance report.
- [ ] **MON-06** Operational reports or dashboards exist for the operations team and application owners. *Needed before: programme end.* Why: Owners need to see health without asking IT. Evidence: Dashboards.

## Backup and DR

Recovery objectives, backup, restore tests, disaster recovery and rollback.

- [ ] **BDR-01** A recovery time and recovery point objective is recorded for each application in the wave and mapped to a backup and replication tier. *Needed before: each wave.* Why: Backup design without objectives is guesswork. Evidence: Objectives table.
- [ ] **BDR-02** Backups are configured for migrated machines and databases, with retention agreed and copies held apart from the workload they protect. *Needed before: each wave.* Why: A backup stored beside the thing it protects fails with it. Evidence: Backup policy, coverage report.
- [ ] **BDR-03** A restore was tested and timed before the first production cutover, and the result recorded. *Needed before: first production wave.* Why: An untested backup is a hope. Evidence: Restore test record.
- [ ] **BDR-04** The disaster recovery design (secondary region or alternative) and failover runbook exist, with a test scheduled. *Needed before: first production wave.* Why: Moving to a single region without a plan can reduce resilience. Evidence: Design, runbook, test date.
- [ ] **BDR-05** The platform itself can be rebuilt: configuration is in code and key and secret stores have recovery protection. *Needed before: first production wave.* Why: Losing the landing zone configuration loses every workload's home. Evidence: Repository, recovery settings.
- [ ] **BDR-06** On premises backups and the source machine are kept until the Azure copy is proven and the rollback window has closed. *Needed before: each wave.* Why: This is the rollback. See the cutover and rollback template. Evidence: Retention note per application.

## Cost management

Budgets, tags, review, licences and commitments.

- [ ] **CST-01** Budgets and alerts exist for each subscription or workload at agreed thresholds. *Needed before: pilot wave.* Why: Cost surprises show up after the invoice unless alerts exist. Evidence: Budget list.
- [ ] **CST-02** Tag coverage is measured and untagged spend reviewed monthly. *Needed before: first production wave.* Why: Untagged spend cannot be charged or challenged. Evidence: Coverage report.
- [ ] **CST-03** A named owner runs a monthly cost review and acts on right-sizing recommendations. *Needed before: first production wave.* Why: Cloud cost drifts upwards without an owner. Evidence: Meeting record.
- [ ] **CST-04** The decision on commitment discounts (reservations, savings plans) is recorded and made only once running data exists. *Needed before: programme end.* Why: Committing before sizing is known locks in waste. Evidence: Decision record.
- [ ] **CST-05** The licence position is confirmed with the vendor or licensing partner, including whether existing licences can be reused (for example through Azure Hybrid Benefit). *Needed before: first production wave.* Why: Licensing can change the run cost more than the infrastructure does. Evidence: Licence statement.
- [ ] **CST-06** A showback or chargeback model is agreed with finance. *Needed before: programme end.* Why: Owners manage cost they can see. Evidence: Finance sign-off.
- [ ] **CST-07** Data transfer costs were reviewed for chatty flows between Azure and the remaining on premises estate. *Needed before: each wave.* Why: Egress is rarely in the first business case. Evidence: Flow analysis, estimate.

## Automation

Infrastructure as code and runbooks.

- [ ] **AUT-01** An infrastructure as code repository exists with review rules and a pipeline identity with least privilege. *Needed before: pilot wave.* Why: Automation with excessive rights is a high-value target. Evidence: Repository settings.
- [ ] **AUT-02** The landing zone can be redeployed from code and drift is detected. *Needed before: first production wave.* Why: A landing zone that cannot be rebuilt is a single point of failure. Evidence: Redeployment test.
- [ ] **AUT-03** Runbooks exist for common operations and for cutover and rollback. *Needed before: each wave.* Why: Runbooks make the 2am version of the job possible. Evidence: Runbook set.

## Operating model

Skills, support and migration tooling.

- [ ] **OPS-01** Skills gaps are identified and a training or partner plan is agreed. *Needed before: pilot wave.* Why: The team that runs it must be able to run it. Evidence: Skills matrix, plan.
- [ ] **OPS-02** The support model is defined: who handles incidents on Azure resources, escalation to vendors and the provider, and the support plan decision. *Needed before: first production wave.* Why: Unclear ownership extends outages. Evidence: Support model document.
- [ ] **OPS-03** Migration tooling is in place: an Azure Migrate project and appliance (or equivalent), source access, and discovery data compared with the inventory. *Needed before: pilot wave.* Why: Discovery finds what the inventory missed. Evidence: Project list, reconciliation note.
