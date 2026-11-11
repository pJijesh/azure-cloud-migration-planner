# Presenting the business case to a CFO

A finance director does not need to hear about migration strategies. They need to know what the organisation is buying, what it costs, what is uncertain, and what they are being asked to approve. This page is a guide to a short, honest case built from the tool's output.

## Lead with the decision, not the technology

State in the first three lines:

1. **The ask.** For example: approve a funded programme of a named size over a named period, with a stage gate after the pilot wave.
2. **The reason.** The risk or cost that exists if nothing is done: out-of-support systems, a hardware refresh due, a contract or site ending. Evidence it from the inventory (for example the number of applications past end of support and what they run).
3. **The range.** The three year cost of the plan against staying, as a range with the biggest assumptions named. Not a single number.

## A one-page structure

| Section | Content | Source in this tool |
|---|---|---|
| Position today | Number of applications, annual run cost, how many are out of support or unconfirmed with their vendor | `assessment.csv`, plan summary |
| Options | Stay as it is; follow the plan; optionally a cheaper partial plan (retire and retain more, move less) | Run `plan` with different rules or overrides |
| Cost over three years | Total, by year, and the **final-year recurring cost**, for each option | `cost_summary.csv` |
| Break even | The month cumulative cost crosses, or "not within three years" stated plainly | `cost_summary.csv` |
| What drives the answer | The two or three assumptions that move it most | `sensitivity.csv` |
| What is not in the numbers | The list of items not modelled, with an estimate where one exists | `plan.md`, "What is not modelled" |
| Risk | What goes wrong, who owns it, how it is reduced (pilot wave, rollback, vendor confirmation) | Dependency warnings, review list |
| Decisions and gates | What is approved now, what comes back for approval, when | Wave plan |

## How to present the numbers

- **Show one-off and run cost separately.** One-off costs (landing zone, migration effort, parallel running, programme management) fall at the start. Run savings arrive later. A single three-year total hides this.
- **Show the final-year run rate.** It is the figure that says what the organisation lives with afterwards.
- **Say when break even is not reached.** A plan that does not pay back in three years can still be right (risk removed, a refresh avoided, a data centre exit), but then the case must be made on those grounds, not on savings.
- **Separate cost avoided from cost reduced.** A refresh that does not have to be bought is a real avoided spend. It belongs in the case, in its own line with its own assumption, and it should be the same figure the finance team would use for the alternative.
- **Use the sensitivity table.** Show what happens when run cost is 20 percent worse or when less on premises cost disappears than hoped. Finance people trust a case that shows its weak spots.
- **State stranded cost honestly.** If data centre, hardware or support contracts do not shrink as applications leave, the saving is smaller. Show the share you assumed to be removed and why.
- **Treat capital and operating differently where finance does.** The tool does not model accounting treatment. Hand the monthly profile (`cost_monthly.csv`) to finance to apply theirs.

## Questions to expect, and honest answers

| Question | A straight answer |
|---|---|
| Will it save money? | Depends on three things: how much on premises cost really goes (stranded cost), what Azure costs once right-sized, and what it costs to get there. Here is the range. Some benefit is risk reduction, not saving |
| Why is year one more expensive than staying? | One-off costs and a period of running both. The plan shows when that reverses, or that it does not within the horizon |
| How sure are the Azure costs? | Run cost factors are placeholders until Azure Migrate (or equivalent) gives estimates per application. Confidence improves as the pilot wave gives real bills |
| What is not included? | Egress, licensing changes, skills, network upgrades, commitments, exit costs and disruption, unless listed under other costs. Give the list |
| Can we stop part-way? | Yes: each wave has a gate. Retained applications and the data centre position at each stage are stated |
| What if a vendor refuses? | The application is retained or replaced. That is in the plan, with a cost, and flagged for review |
| What is the downside? | Name it: a failed cutover, a licence cost, a slower programme. Give the mitigation and the rollback |
| What do we commit to now? | The landing zone and the pilot wave. The rest is released at the gate |

## Things not to do

- Do not present illustrative or placeholder numbers as estimates. The tool labels them, and so should the slide.
- Do not quote a savings percentage you cannot trace to an input.
- Do not leave the hybrid running cost, the parallel run or the programme team out because they are awkward.
- Do not claim the cloud is cheaper as a matter of principle. It is cheaper or dearer for particular applications under particular assumptions.
- Do not hide the applications you are not moving, and the cost of keeping them.

## Before the meeting

1. Replace every placeholder in the assumptions file with a quote, a contract figure or an Azure Migrate estimate, and keep the source for each.
2. Agree with finance how on premises cost was allocated to applications, and use the same method for all of them.
3. Rerun the plan, and keep the output folder with its input hashes as the audit trail.
4. Have the owner of each assumption in the room, or have their answer written down.
