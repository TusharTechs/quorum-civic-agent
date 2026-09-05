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

---

# Day 3 — lineage resolution + version diff (Tier 1 item #3)

## Cross-meeting entity resolution — WORKING
Resolved 96 items across three meetings (2026-03-10, 2026-03-24, 2026-06-30)
into 93 lineages, **2 of which genuinely span meetings**. Identity is
established deterministically (BMC section, ordinance number) and is therefore
auditable; the LLM is never used to decide identity, only to explain a diff.

### Lineage A — BMC 23.324.050 (zoning)
| | 2026-03-10 | 2026-03-24 |
|---|---|---|
| item number | 14 | 1 |
| ordinance | *(none)* | 8,003-N.S. |
| calendar | Action / public hearing | Consent |
| page | 9 | 3 |

The draft in the first-reading packet is literally headed **"ORDINANCE NO.
-N.S."** - a blank identifier. The decision has no number until it passes.
That is the "no shared key" argument in one screenshot.

### Lineage B — BMC 2.12 (Berkeley Election Reform Act)
item 15 -> item 2, gained Ordinance 8,004-N.S., public hearing -> second reading.

### Rejected: a false lineage, and why it matters
"Minutes for Approval" matched itself across 2026-03-24 and 2026-06-30 at title
similarity 1.00. It is a standing fixture, not one decision travelling. Lineages
now carry a `confidence`: **strong** only when a hard identifier (BMC section or
ordinance number) ties versions together; title similarity alone is **weak** and
excluded by default. Worth saying out loud in the video - the resolver knows the
difference between a recurring agenda item and a tracked decision.

## Version diff — WORKING, and it says "no amendment"
The `Recommendation:` line is only a summary. A real amendment appears in the
**enacting text**, so the diff compares that. In a first-reading packet the
draft ordinance is embedded inside a staff report with no closing heading, so
the body must be bounded by content, not page count.

Result for Lineage A: enacting text **97.84% similar**, 3 change blocks, **all
three page furniture** ("Page 6 of 11" vs "Page 1 of 2"). Verdict:
`amended_between_readings: false`.

**This is a correct and honest answer, and the machinery is right.** But it is
not yet the §10 centrepiece beat, which needs a lineage whose *content* changed.

## Outcome extraction — WORKING (Tier 1 item #5, earlier than planned)
The second-reading packet carries the recorded vote verbatim, so the Civic
Change Graph `outcome` field fills without needing the minutes:

    ayes   Bartlett, Blackaby, Humbert, Kesarwani, Lunaparra,
           O'Keefe, Taplin, Tregub, Ishii
    noes   none      absent none      tally 9-0    source page 19

## Next: find a lineage with real content change
Best lead is Berkeley's **"Revised Agenda Material"**, published in Supplemental
Packets 1 and 2 between the original packet and the vote. That is where an item
is actually rewritten before the vote, and it lines up exactly with the tiered
deadlines in §6 - the revision lands *after* most people have read the original.
That is the true "the provision you supported is gone" beat, and it is a
stronger story than a first/second reading diff because the change arrives
inside the comment window.

---

# THE CENTREPIECE — found and verified (2026-09-05)

**Item 46, 30 June 2026 — Surveillance Technology Ordinance: Community Video
Streams (BPD Policy 1306 / LESM 355) and Investigative Software.**

A police surveillance policy that was **materially rewritten between two
published packets**, where the rewrite answers specific public-committee
requests. Every step is citable to a page in a public PDF.

## The chain

**7 May 2026** — Council refers the Community Video Streams Acquisition Report
and Surveillance Use Policy to the Public Safety Policy Committee.
Policy text: `2026-05-07 Revised Special Agenda Packet`, pp.125-137.

**Public Safety Committee** asks for five specific revisions (carried verbatim
in the 30 June packet, item 46, `Policy Committee Recommendation:`, p.18):
  1. Clarify how participating camera locations will be verified and address
     liability if cameras are moved
  2. Develop a process for notifying camera owners when footage is accessed
  3. Remove vendor-specific references from the acquisition report
  4. Clarify policies governing access to real-time / live video monitoring
  5. Provide additional information regarding the use of artificial intelligence

**30 June 2026** — staff return with redlined policy. The staff memo at **p.1395**
states what the redline does, and it maps directly onto the committee's asks:
  - "To generalize references in the CVS acquisition report and to clarify that
     no vendor selection has been made or is implied."        -> request 3
  - "To require prompt disconnection of any integrated camera found to have been
     repositioned to capture an area where a reasonable expectation of privacy
     exists."                                                  -> request 1
  - "To clarify that real-time access to live video streams is permitted only
     when there is an active CAD incident or call..."          -> request 4

## The verified diff

New operative sentence, **absent from the 7 May packet, present in the 30 June
packet**:

> "Upon discovery that an integrated camera has been repositioned to capture an
> area where a reasonable expectation of privacy exists, the Department shall
> immediately pause that camera's integration until the camera is positioned in
> compliance with this policy."

| Packet | Contains the clause? | Pages |
|---|---|---|
| 2026-05-07 Revised Special Agenda Packet | **NO** | - |
| 2026-06-30 Agenda Packet | **YES** | 1395, 1402, 1413, 1415 |
| 2026-06-30 Revised Agenda Packet | **YES** | 1419, 1426, 1437, 1439 |

Verified by exact-string search over our own extracted text, both directions.

## Why this is the right centrepiece

1. **The change is real and substantive** - a new privacy safeguard on police
   camera integration, not a renumbering.
2. **It is causally traceable.** A committee asked; the department answered;
   the answer is in the text. QUORUM can report *which of the five requests
   survived* - that is the Impact Ledger, on real data, across two months.
3. **A judge can verify it in ninety seconds.** Open two public PDFs, search one
   sentence, find it in one and not the other.
4. **It inverts the brief's example productively.** §10 imagined "the provision
   you supported is gone." Here it is "the safeguard the committee asked for was
   added, and two of the five asks are not visibly addressed." Both directions
   are the same capability, and the honest version is more interesting.
5. **Identity drifted too**: the same policy is "LESM 355" in May and
   "BPD Policy 1306" in June. Renumbering, on the centrepiece item.

## Open items on this lineage
- Requests 2 (notifying camera owners) and 5 (AI use) are not in the staff
  memo's change list. Confirm whether they appear in the policy text; if not,
  that is precisely the "you asked, it did not happen" beat.
- The May policy extraction (pp.125-137) over-runs into the adjacent
  Investigative Software policy. Bound extraction per-policy before quoting a
  similarity number.

## Segmenter limitation found
The 2026-05-07 special-meeting packet segments to **0 items** - special meetings
number items "1a", "1b" rather than "1.". The segmenter needs a special-meeting
pattern before it can claim general coverage.

---

# THE IMPACT LEDGER — verified, 11 requests tracked (2026-09-05)

Correction to the entry above: the Public Safety Policy Committee made
**eleven** requests, not five. The segmenter captured the full 1,326-character
`Policy Committee Recommendation:` field correctly; the earlier count came from
truncating the display.

## The real chain
- **7 May 2026** - Council acts on public safety technology package; CVS policy
  referred to PSPC via the Mayor's supplemental memorandum.
  Policy text: `2026-05-07 Revised Special Agenda Packet`, **pp.125-129**.
- **2 June 2026** - PSPC reviews and issues **11 requested revisions**
  (Vote: All Ayes). Listed verbatim: 30 June packet **p.18** (agenda listing)
  and **pp.1391-1392** (staff report).
- **30 June 2026** - Department returns redlined policy + written responses.
  Policy text: `2026-06-30 Agenda Packet`, **pp.1414-1419**.

## Bounded diff (per-policy, section series 355.x)
MAY 12,315 chars (pp.125-129) vs JUNE 15,183 chars (pp.1414-1419)
**similarity 0.8957**, 16 change blocks, **6 substantive additions**:

1. Pause integration of a camera repositioned to capture a private area
2. **First Amendment protection** - no monitoring of lawful protests,
   demonstrations or political gatherings
3. Retention period tied to statute of limitations for the underlying offence
4. **72-hour notification** to City Manager, City Attorney and Council if a
   Federal Agency is given BPD-owned CVS data
5. Audit frequency "biennial" -> "twice a year"
6. OSPA audits must sample access logs to verify queries tie to a valid case

## Ledger: request -> what actually happened
| # | Committee asked | Outcome in the 30 June text |
|---|---|---|
| 1 | verify camera locations / moved cameras | **ADDED** (addition 1) |
| 2 | notify camera owners when footage accessed | **DOWNGRADED** - see below |
| 3 | remove vendor-specific references | **ADDED** (staff memo p.1395) |
| 4 | real-time / live access rules | **ADDED** (staff memo p.1395) |
| 5 | AI use + human oversight | **prose response only** (p.1394), not policy text |
| 8 | strengthen audit provisions | **ADDED** (additions 5, 6) |
| 9 | 72-hour immigration-related language | **ADDED** (addition 4) |
| 11 | retention periods / liability | **ADDED** (addition 3) |
| 6, 7, 10 | investigative software / audio | concern Policy 1307 - not yet diffed |

## The centrepiece line — request 2, verbatim from p.1394
> "At the request of the PSPC, the Department will include in the RFP a request
> for vendors to describe the feasibility of notifying camera owners each time
> BPD personnel access their feed. **This is not a minimum requirement for
> vendor selection** but will be evaluated as a value-added feature..."

The committee asked for a *process*. What appears is a *feasibility question to
vendors, explicitly not required*. The provision was not deleted - it was
quietly demoted. That is §10's "the provision you supported is gone", except it
is real, it is citable to one page, and it is more interesting than deletion
because a reader skimming the response would think the request was granted.

## Why this is unfakeable
Two public PDFs, two months apart, 176 and 1,790 pages. A judge opens both,
searches one sentence, and sees it in one and not the other. No mock, no API,
no staged data.
