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
