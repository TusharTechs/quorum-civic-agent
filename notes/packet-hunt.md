# Packet hunt — Day 0 findings
Retrieved: 2026-09-05. Jurisdiction: Berkeley, CA.

## Verdict
**Lead meeting: 30 June 2026 Regular Meeting.** Satisfies (a), (b), (c) and gives
a stronger Code Interpreter beat than the brief's generic "water rate" example.
(d) still open. (e) candidate identified.

## (a) Comment channel + deadlines — CONFIRMED
- Email: council@berkeleyca.gov  (stated on the agenda itself, not a third party)
- Supplemental packet tiers, per the agenda text:
  - 5:00pm **five days** before the meeting  -> Supplemental 1
  - 5:00pm **the day before**                -> Supplemental 2
  - 5:00pm **two days AFTER** the meeting    -> Supplemental 3 (after the vote)
- NOTE: brief §6 says "7 days / 12pm day before". Site says five days / 5pm.
  Re-verify against the packet PDF cover text before hardcoding the countdown.

## (b) Multi-meeting lineage WITH renumber — CONFIRMED, two independent examples
1. Zoning: "Amendments to BMC Title 23 (Zoning) to Update the Regulation of
   Nonconforming Lot Coverage, Floor Area Ratio and Density for Residential Uses
   in Selected Zoning Districts"
   -> first reading (unnumbered agenda item, "First Reading Vote: All Ayes")
   -> second reading 2026-03-24 as **Ordinance 8,003-N.S.**, Item 1
2. Tax rates: "FY 2027 Special Tax Rate: Library Relief Act of 2024 (Measure X)"
   (2026-06-30 Item 2) -> **Ordinance 8,013-N.S.**
   "FY 2027 Special Tax Rate: Library Services" (Item 3) -> **Ordinance 8,014-N.S.**
   "FY 2027 Tax Rate: Emergency Services for the Severely Disabled" (Item 7)
   -> **Ordinance 8,018-N.S.**
   Same substance, three different identifiers, no shared key. This is the
   drifting-identity case the Civic Change Graph exists to resolve.

## (c) Costed household table — CONFIRMED, and better than expected
Eleven FY2027 per-square-foot rates on DWELLING UNITS, all on the 30 June agenda,
all on the CONSENT CALENDAR (i.e. passed without discussion):

| Item | Measure                                   | $/sq ft dwelling |
|------|-------------------------------------------|------------------|
| 2    | Library Relief Act 2024 (Measure X)       | 0.06297          |
| 3    | Library Services                          | 0.3128           |
| 7    | Emergency Svcs, Severely Disabled (Meas E)| 0.02339          |
| 8    | Fire Protection / Emerg Response (Meas GG)| 0.07026          |
| 9    | Firefighting / Wildfire Prev (Measure FF) | 0.13633          |
| 10   | Emergency Medical Services (Paramedic)    | 0.0492           |
| 12   | Parks, City Trees and Landscaping         | 0.2783           |
| 14   | SAFE STREETS (Measure FF)                 | 0.17842          |

Sum of the above ~= $1.0289 / sq ft / year.
=> a 1,450 sq ft dwelling pays ~$1,492/yr in city special taxes.
Plus items 4, 5, 6, 11, 13, 15 (bonds / non-dwelling) to be checked.

Why this is the right beat:
- Arithmetic no resident ever does: the cost is SPREAD ACROSS ELEVEN SEPARATE
  AGENDA ITEMS. No single item states the household total.
- Diffable: FY2026 rates vs FY2027 rates gives a year-over-year delta per household.
- Narrative: eleven taxes on every homeowner, buried in a 42-item consent calendar.

## (e) Two costed alternatives — CANDIDATE
Item 17: "Transactions and Use (Sales) General Tax Measure - November 3, 2026
Ballot" — 0.5% increase taking the aggregate rate to 10.75%. Check the staff
report for a costed alternative rate.

## (d) Missing / broken exhibit — STILL OPEN
Not yet found. Search strategy: fetch the full 30 June packet PDF, extract every
"Attachment"/"Exhibit" reference, then check which referenced attachments are
absent from the packet or return 404. This is mechanical and is genuinely the
first thing the ingest code should do anyway.

## Other high-stake items on 30 June 2026 (for stake matching)
- Item 1:  Repeal and Reenact BMC Ch 14.52 — goBerkeley Parking Management Program
           (street parking — matches the brief's demo archetype)
- Item 40: Support for CA SB 1383 (Housing Development Density Bonus)
- Item 45: Initiative Ordinance Amending Rent Stabilization Ordinance (Nov 2026 ballot)
- Item 46: Surveillance Technology Ordinance — video streams / investigative software
- Item 29: North Berkeley BART Affordable Housing — predevelopment funding

## URL patterns (for the Watcher)
- Agenda index:   /your-government/city-council/city-council-agendas
- eAgenda (HTML): /city-council-regular-meeting-eagenda-{month}-{d}-{yyyy}
- Packet PDF:     /sites/default/files/city-council-meetings/{YYYY-MM-DD} Agenda Packet - Council - WEB.pdf
- Annotated:      /sites/default/files/city-council-meetings/{YYYY-MM-DD} Annotated Agenda - Council.pdf
- Item PDF:       /sites/default/files/{YYYY-MM}/{YYYY-MM-DD} Item {NN} {Title}.pdf
- Supplemental:   /sites/default/files/legislative-body-meeting-attachments/...
- Email alerts:   govdelivery topic CABERKE_18

## Sources
- https://berkeleyca.gov/your-government/city-council/city-council-agendas
- https://berkeleyca.gov/city-council-regular-meeting-eagenda-june-30-2026
- https://berkeleyca.gov/city-council-regular-meeting-eagenda-march-24-2026

---

# Day 1 — ingest measurement (2026-09-05)

Ingested the real 30 June 2026 packet. **The brief's §9 size assumption is wrong
by an order of magnitude and the cost model needs restating.**

| Measure          | Brief §9 assumption | Actual (2026-06-30 Berkeley) |
|------------------|---------------------|------------------------------|
| Pages            | ~300                | **1,790**                    |
| File size        | not stated          | **62.2 MB**                  |
| Characters       | —                   | 7,632,405                    |
| Est. tokens      | ~200,000            | **~1,908,000  (9.5x)**       |
| Image-only pages | —                   | 42 (<50 chars)               |

sha256 df379687006c6d3f... retrieved 2026-09-05T11:48Z

## What this changes

1. **Never send a whole packet to Sonnet.** One full pass would be ~$3.80 input
   alone. §9's "naive $1.80/run" is really ~$8/run at this size.
2. **Routing still holds and is now the whole ballgame.** Nova Lite over the full
   text is ~$0.11 input. Deep-read stays scoped to candidate items only
   (3 items x ~20pp x ~700 tok = ~42k tok -> ~$0.08 on Sonnet).
   Target remains well under $0.50/run.
3. **Segment from structure, not brute force.** The agenda item list sits in the
   first ~30 pages. Segment off that plus page headers rather than streaming
   1.9M tokens through any model.
4. **The OCR fallback error edge has real material** — 42 image-only pages,
   running in consecutive even numbers from p.40 (scanned attachments). This is
   Tier 2 item #7, and it is genuine, not manufactured.

## Demo impact — this is an upgrade

§10's opening beat says "the real 312-page packet". The true number is **1,790
pages**. Use it. "Your city published 1,790 pages on Tuesday. Nine people read
it." is a stronger and *verifiable* opening line.

## Operational note for the Watcher
Berkeley's WAF returns **403 to HEAD requests**. Probe with a ranged GET
(`Range: bytes=0-2047`) plus a browser User-Agent. Plain GET on HTML is fine.

---

# Day 1 result — segmentation + verified household arithmetic

## Segmentation (Tier 1 item #1) — DONE
51 of 51 agenda items extracted from the 1,790-page packet by **pure structure,
zero LLM cost**. Berkeley's front matter (pp.3-19) is rigidly formatted:

    N.
    <title>
    From: / Recommendation: / Financial Implications: / Contact:

Sub-items nested inside a Recommendation (items 31 and 46 each contain their own
1./2./3. lists) are rejected by requiring item numbers to run consecutively.
Output: `data/cache/items_2026-06-30.json`.

## Household cost — hunt criterion (c) CONFIRMED, with a correction

A naive regex over "per square foot" gives the WRONG answer. The 15 tax-rate
items use **three different rate bases**, and they must be separated:

**A. Per square foot of dwelling improvements — 8 items, these apply to a home**

| Item | Ordinance   | $/sq ft | Basis                              |
|------|-------------|---------|------------------------------------|
| 2    | 8,013-N.S.  | 0.06297 | for dwelling units                 |
| 3    | 8,014-N.S.  | 0.31280 | for dwelling units                 |
| 7    | 8,018-N.S.  | 0.02339 | of improvements                    |
| 8    | 8,019-N.S.  | 0.07026 | of improvements for dwelling units |
| 9    | 8,020-N.S.  | 0.13633 | of improvements                    |
| 10   | 8,021-N.S.  | 0.04920 | of improvements                    |
| 12   | 8,023-N.S.  | 0.27830 | of improvements                    |
| 14   | 8,025-N.S.  | 0.17842 | of dwelling unit improvements      |
|      | **TOTAL**   | **1.11167** |                                |

**B. Percent of assessed value (ad valorem) — 5 items**
items 5, 6, 11, 13, 15 -> 0.0075 + 0.0200 + 0.0140 + 0.0035 + 0.0040
= **0.0490% of assessed value**

**C. Excluded — do NOT count toward a household**
- item 4  (8,015-N.S.) $0.9168/sq ft — **large non-profits only**, not dwellings
- item 20 TNC user tax — 65.1005c per trip, not property

### Worked example
A 1,450 sq ft home assessed at $1.2M:
  1,450 x $1.11167          = $1,611.92
  $1,200,000 x 0.0490%      =   $588.00
  **TOTAL ~ $2,199.92 / year**, spread across **13 separate agenda items**,
  all of them on the consent calendar.

### Why this is the Code Interpreter beat
Getting it right requires distinguishing three rate bases across 15 items and
excluding a $0.9168 rate that looks like the biggest one but applies to
non-profits. A naive sum overstates a 1,450 sq ft household by **$1,329/year**.
That is genuine reasoning on real data, and it is checkable by any judge.

## Bedrock
Anthropic use case form propagated; Sonnet, Haiku and Strands streaming all
confirmed working in us-west-2.

---

# Day 2 result — stake matching (Tier 1 item #2) — DONE

Two-stage routed pipeline, per §9:
  triage : Nova Lite over all 51 items (title + first 600 chars of recommendation)
  brief  : Claude Sonnet 4.5 over survivors only, producing WHAT / WHY YOU /
           WHY NOW / EVIDENCE with a verbatim quote and a page-anchored URL.

**Attention efficiency on a real packet: 1,790 pages -> 51 items -> 6 candidates
-> 2 decisions.**  Cost: **$0.0200 per run** (target was <$0.39).

## Consolidation is the differentiator
First version emitted five near-identical alerts, one per tax item. Tier 1 #2
says surface 1-2 items, so alerts are now keyed to a **decision**, not an agenda
item: the FY2027 tax rates collapse into one alert stating the combined
household effect. A summariser cannot do this - it has no household to sum
against. This is also the Attention Efficiency beat (Tier 2 #10).

## Known weakness — triage recall is unstable
Across three runs Nova Lite returned 5, then 16, then 6 candidates from the same
51 items. In the 6-candidate run it caught only 4 of the 8 per-sq-ft dwelling
taxes, so the consolidated total read $1,207 rather than the true $1,611.92.

Not a blocker, but this is the single biggest quality risk in the pipeline, and
it is exactly what the Evaluations harness (Tier 3 #12) exists to measure.
Cheap mitigations, in order:
  1. temperature=0 on the triage model
  2. deterministic pre-filter: any item whose recommendation matches a
     rate/fee/tax pattern always reaches the deep pass, no LLM judgement
  3. score the deep pass against a hand-labelled key for this packet

## API note
`Agent.structured_output()` is deprecated in strands-agents 1.54. Use
`agent(prompt, structured_output_model=Model)`, which returns an AgentResult
carrying both `.structured_output` and `.metrics.accumulated_usage`. The
deprecated path returns the model only, and token metrics read as zero - which
silently breaks the §9 cost counter.
