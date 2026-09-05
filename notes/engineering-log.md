# QUORUM — engineering log

A record of what was measured, what was verified, and what broke. Every number
here was produced by code in this repository against public documents, and can
be reproduced by re-running the scripts in `scripts/`.

Jurisdiction: **Berkeley, California**. Chosen because it closes the loop with
public data alone — a published comment address, hard tiered deadlines, and
comments republished into the record as Supplemental Packets, so verification
needs no API and no private access.

---

## 1. The source documents

| Packet | Pages | Size | Items segmented |
|---|---|---|---|
| 2026-03-10 Agenda Packet | 1,146 | 164.8 MB | 18 |
| 2026-03-24 Agenda Packet | 586 | 49.1 MB | 27 |
| 2026-05-07 Revised Special Agenda Packet | 176 | 4.6 MB | 0 (see limitations) |
| 2026-06-30 Agenda Packet | 1,790 | 65.2 MB | 51 |
| 2026-06-30 Revised Agenda Packet | 1,814 | 66.2 MB | 51 |

Public comment address, stated on the agenda itself: `council@berkeleyca.gov`.

Supplemental packet deadlines. Submission cut-offs and distribution dates are
different things, and conflating them produces a wrong countdown:

| Submit by | Appears in | Distributed |
|---|---|---|
| 5:00pm, seven days before | Supplemental Packet 1 | five days before |
| 12:00pm, the day before | Supplemental Packet 2 | 5:00pm the day before |
| after that | Supplemental Packet 3 | two days **after** the meeting |

Packet 3 lands after the vote. Any "why now" countdown must use the submission
cut-off, not the distribution date.

### Fetching: Berkeley's WAF rejects HEAD

`HEAD` requests return 403 for every packet URL. `GET` succeeds normally,
including ranged requests. The watcher therefore probes with a ranged `GET` plus
a browser User-Agent, never `HEAD`. Plain `GET` on HTML pages is fine.

### Scale

The 30 June packet is **7,632,405 characters ≈ 1.9M tokens**. A single pass of
one packet through a frontier model would cost roughly **$3.80 in input alone**.
This is the entire justification for the model routing in section 3: structure is
extracted in Python at zero cost, triage runs on a cheap model, and only the
handful of surviving items reach an expensive one.

**42 pages carry no extractable text** (under 50 characters), running in
consecutive even numbers from page 40 — scanned attachments. These are what the
OCR fallback path exists for.

---

## 2. Segmentation — deterministic, no model

Berkeley's front matter is rigidly formatted, so items are extracted in pure
Python:

```
N.
<title, one or more lines>
From: / Recommendation: / Financial Implications: / Contact:
```

51 of 51 items recovered from the 1,790-page packet at zero model cost.

Two boundary bugs found and fixed:

- **Nested sub-items.** Items 31 and 46 each contain their own numbered lists
  inside a Recommendation. Requiring item numbers to run *consecutively* rejects
  these; a bare "numbered line" rule does not.
- **Tail bleed.** The final item absorbed everything after the listing — legal
  notices, adjournment text, minutes. Fixed by bounding the listing at
  `Public Comment – Items Not Listed`, `Adjournment` or
  `NOTICE CONCERNING YOUR LEGAL RIGHTS`.

---

## 3. Stake matching and household arithmetic

Two stages, routed by cost: **Nova Lite** over every item (title plus the first
600 characters of the recommendation), then **Claude Sonnet 4.5** over the
survivors only.

Measured on the 30 June packet:

```
1,790 pages -> 51 items -> 12 candidates -> 3 decisions     $0.0200 per run
```

### Alerts are keyed to decisions, not agenda items

The first version emitted five near-identical alerts, one per tax item. Alerts
are now grouped by *decision*: the FY 2027 tax rates collapse into a single
alert stating the combined household effect. A summariser cannot do this,
because it has no household to sum against.

### The rate arithmetic has three bases, and conflating them is wrong

The 30 June packet sets fifteen tax rates. A naive regex over "per square foot"
yields **$1.85/sq ft**. The correct figure is **$1.11167/sq ft**.

**A. Per square foot of dwelling improvements** — applies to a home

| Item | Ordinance | $/sq ft |
|---|---|---|
| 2 | 8,013-N.S. | 0.06297 |
| 3 | 8,014-N.S. | 0.31280 |
| 7 | 8,018-N.S. | 0.02339 |
| 8 | 8,019-N.S. | 0.07026 |
| 9 | 8,020-N.S. | 0.13633 |
| 10 | 8,021-N.S. | 0.04920 |
| 12 | 8,023-N.S. | 0.27830 |
| 14 | 8,025-N.S. | 0.17842 |
| | **total** | **1.11167** |

**B. Percent of assessed value** — items 5, 6, 11, 13, 15 → **0.0490%**

**C. Excluded** — item 4 (8,015-N.S., $0.9168/sq ft) applies to **large
non-profits only**; item 20 is a per-trip tax on ride-hailing.

Item 4 is the trap: it is the largest rate on the page and is phrased almost
identically to the others. Counting it overstates a 1,450 sq ft household by
**$1,329/year**.

Worked example — 1,450 sq ft home assessed at $1.2M:

```
1,450 x $1.11167        = $1,611.92
$1,200,000 x 0.0490%    =   $588.00
                          ---------
                          $2,199.92 / year
```

spread across **13 separate agenda items**, all on the consent calendar — which
means they pass without discussion, and no single document states the total.

---

## 4. Cross-meeting entity resolution

The same decision reappears across meetings under a different item number, a
different calendar, and eventually an ordinance number it did not previously
have. There is no shared key.

Identity is established **deterministically** — BMC section, ordinance number —
never by a model, because identity must be auditable. A model is used only to
explain a diff.

Across three meetings (96 items into 93 lineages), two genuinely span meetings.

**BMC 23.324.050 — zoning**

| | 10 March | 24 March |
|---|---|---|
| item number | 14 | 1 |
| ordinance | *none* | 8,003-N.S. |
| calendar | Action / public hearing | Consent |
| page | 9 | 3 |

In the first-reading packet the draft is headed literally `ORDINANCE NO. -N.S.`
The decision has no identifier until it passes.

**BMC 2.12 — Berkeley Election Reform Act**: item 15 to item 2, gained Ordinance
8,004-N.S., public hearing to second reading.

### A false lineage, and the fix

"Minutes for Approval" matched itself across two meetings at title similarity
1.00. It is a standing fixture, not one decision travelling. Lineages now carry
a confidence: **strong** only when a hard identifier ties versions together;
title similarity alone is **weak** and excluded by default.

### Diffing the right text

`Recommendation:` is only a summary. A substantive amendment appears in the
**enacting text**, so that is what is compared. In a first-reading packet the
draft ordinance is embedded inside a staff report with no closing heading, so
the body must be bounded by content, not by page count — two earlier attempts
produced garbage by running into an adjacent ordinance and then to the end of a
1,146-page packet.

Result for BMC 23.324.050: enacting text **97.84% similar**, three change
blocks, **all three page furniture**. Verdict: not amended between readings. A
correct answer, and a useful one — but not a content change.

### Outcome extraction

The second-reading packet carries the recorded vote verbatim, so outcomes are
available without the minutes:

```
ayes    Bartlett, Blackaby, Humbert, Kesarwani, Lunaparra,
        O'Keefe, Taplin, Tregub, Ishii
noes    none     absent none     tally 9-0     source page 19
```

---

## 5. The tracked decision: a police surveillance policy

The clearest case of a decision genuinely changing between publications.

**7 May 2026** — Council refers the Community Video Streams Acquisition Report
and Surveillance Use Policy to the Public Safety Policy Committee. Policy text:
7 May packet, **pp.125–129**.

**2 June 2026** — the committee issues **eleven requested revisions** (Vote: All
Ayes), carried verbatim in the 30 June packet at **p.18** and **pp.1391–1392**.

**30 June 2026** — the department returns a redlined policy. Policy text:
**pp.1414–1419**. The same document is *LESM 355* in May and *BPD Policy 1306*
in June — the policy is itself renumbered.

### Bounded diff

May 12,315 chars vs June 15,183 chars, **similarity 0.8957**, 16 change blocks,
**6 substantive additions**:

1. Pause integration of a camera repositioned to capture a private area
2. **First Amendment protection** — no monitoring of lawful protests,
   demonstrations or political gatherings
3. Retention tied to the statute of limitations for the underlying offence
4. **72-hour notification** to City Manager, City Attorney and Council if a
   federal agency is given BPD camera data
5. Audit frequency "biennial" changed to "twice a year"
6. Audits must sample access logs to verify queries tie to a valid case number

### Ledger: what was asked, and what happened

| # | Requested | Outcome in the 30 June text |
|---|---|---|
| 1 | verify camera locations / moved cameras | added |
| 2 | notify camera owners when footage accessed | **downgraded** |
| 3 | remove vendor-specific references | added |
| 4 | real-time / live access rules | added |
| 5 | AI use and human oversight | prose response only, not policy text |
| 8 | strengthen audit provisions | added |
| 9 | 72-hour immigration-related language | added |
| 11 | retention periods / liability | added |
| 6, 7, 10 | investigative software / audio | concern Policy 1307, not yet diffed |

### The downgrade, verbatim from p.1394

> "At the request of the PSPC, the Department will include in the RFP a request
> for vendors to describe the **feasibility** of notifying camera owners each
> time BPD personnel access their feed. **This is not a minimum requirement for
> vendor selection** but will be evaluated as a value-added feature..."

A *process* was requested. A *non-binding feasibility question to vendors*
appeared. The provision was not deleted; it was demoted. A reader skimming the
response would conclude the request had been granted.

### Reproducing it

The clause `repositioned to capture an area` is **absent** from the 7 May packet
and **present** in the 30 June packet at pages **1395, 1402, 1413, 1415** (and
at 1419, 1426, 1437, 1439 in the revised June packet). Verified by exact-string
search over extracted text, in both directions.

### On the revised packet

The 30 June packet was republished 24 pages longer. The page-level diff isolated
the change immediately: `REVISED TO ADD A TELECONFERENCE LOCATION`. A Brown Act
notice, no policy content. Reporting accurately that a change does not matter is
as useful as reporting one that does.

---

## 6. The pipeline as a Strands Graph

`src/quorum/pipeline.py`. The `Graph` is the coordinator; there is no supervisor
agent layered on top of it.

| Node | Type | Rationale |
|---|---|---|
| watch, ingest, segment | `MultiAgentBase` | Deterministic, free, auditable |
| triage | Nova Lite | High volume, low visibility |
| deep_read | Claude Sonnet 4.5 | The output a person reads |
| ocr_fallback, archive | `MultiAgentBase` | Terminal states |

A deterministic node still reports an `AgentResult`, because downstream nodes
read prior output in that shape — so code nodes and agent nodes are
interchangeable to the Graph.

Three paths, each verified by execution:

```
normal      watch -> ingest -> segment -> triage -> deep_read   5 nodes, $0.0215
error edge  watch -> ingest -> ocr_fallback                     3 nodes, halts
archive     watch -> ingest -> segment -> triage -> archive     5 nodes, $0.0000
```

The error edge fires when the share of image-only pages crosses a threshold; the
run stops rather than reasoning over text it cannot trust. The archive path is
the cheapest run in the system: when nothing affects the household, nothing is
spent and the system says so.

`set_max_node_executions(24)` and a 900-second timeout are set explicitly —
Strands warns when they are absent, because the lifecycle permits cycles.

---

## 7. Bounded autonomy

### Cedar is the real engine

`cedarpy` evaluates `policy/quorum.cedar` with the actual Cedar engine — not a
hand-rolled approximation. Cedar is deny-by-default: an action with no matching
permit is refused. All five branches verified:

| Scenario | Decision |
|---|---|
| draft, no standing | permitted — drafting is reversible and private |
| submit, approved, no standing | **blocked** |
| submit, verified resident, all conditions met | permitted |
| submit, standing but an uncited claim | **blocked** |
| submit, approval 30h old (limit 24h) | **blocked** |

### Interrupts survive process death

Verified across two separate OS processes: one raised
`tool_context.interrupt(...)` and exited; a second resumed the same session from
`FileSessionManager` on disk and completed the tool call.

### Grounding is checked in code, not by prompting

| Input | Result |
|---|---|
| legitimate comment, 3 quotes, cited | passes |
| uncited factual claim about the packet | caught |
| fabricated quote not present in the packet | caught |

The rule: **cite what the packet says; you need not cite your own life or your
own opinion.** A sentence requires a citation only if it quotes the packet or
makes a factual claim about the document, and is not normative.

The first version demanded a citation for *every* sentence, flagging "My
household has no driveway" and "I urge the Council to…" as ungrounded. A gate
that blocks every legitimate comment is worse than no gate — it trains the
operator to override it.

### End to end

```
DRAFT      Sonnet, 3 verbatim quotes, all cited (packet p.3)
GROUNDING  3/3 quotes verified, 0 uncited claims
INTERRUPT  "Approve filing this comment into the public record?"
APPROVED   resumed mid-tool, in a different OS process
CEDAR      BLOCKED - no verified standing in this jurisdiction
OUTCOME    comment prepared, not filed
```

The refusal rests on standing alone: the draft is fully grounded and a human
approved it, and it is still refused, because the operator has no stake in this
jurisdiction.

---

## 8. Defects found and fixed

1. **Rate-basis conflation.** Summing all "per square foot" rates included a
   non-profit tax, overstating a household by $1,329/year. Caught by reading the
   rate basis of every item rather than trusting the pattern.
2. **Sentence splitting on abbreviations.** "8 p.m." and "(packet p.3)" were
   treated as sentence ends, manufacturing uncited fragments from properly cited
   sentences.
3. **Literal control characters in regexes.** A patching mistake wrote backspace
   (0x08) into eight patterns in place of a word-boundary escape, so the
   packet-claim detector silently never matched — the grounding gate would have
   passed everything. A negative control caught it. Without that control it
   would have shipped looking perfect.
4. **Deprecated structured output.** `Agent.structured_output()` is deprecated in
   strands-agents 1.54 and returns **zero token metrics**, silently breaking cost
   accounting. The supported call is
   `agent(prompt, structured_output_model=Model)`, which returns an `AgentResult`
   carrying both `.structured_output` and `.metrics.accumulated_usage`.
5. **Unbounded ordinance extraction.** Fixed page windows ran into adjacent
   ordinances and, in one case, to the end of a 1,146-page packet.

---

## 9. Known limitations

- **Triage recall is unstable.** Across runs on identical input, Nova Lite
  returned 5, 16, 12 and 6 candidates. In the 6-candidate run it caught only four
  of the eight dwelling taxes, so the consolidated total read $1,207 rather than
  $1,611.92 — correct arithmetic over an incomplete set. Planned fixes, in order:
  `temperature=0`; a deterministic pre-filter so any item matching a rate, fee or
  tax pattern always reaches the deep pass regardless of model judgement; then
  scoring against a hand-labelled key.
- **Special-meeting packets are not segmented.** They number items `1a`, `1b`
  rather than `1.`, so the 7 May packet yields zero items. Its policy text is
  still located and diffed by content.
- **The OCR fallback does not yet OCR.** The edge fires correctly and the run
  halts with "evidence incomplete" rather than proceeding on unverified text.
- **Policy 1307 (Investigative Software) has not been diffed**, so three of the
  eleven ledger rows are unresolved.
- **Requests answered in prose are not tracked automatically.** Request 5 (AI
  oversight) is addressed at p.1394 but not in the policy text; the ledger
  currently distinguishes this by hand.

---

## 10. Verification: what the council actually did

Berkeley publishes an **Annotated Agenda** after each meeting recording the
action taken on every item. It parses with the same segmenter as the agenda
packet — the only change needed was two extra field labels, `Action:` and
`Recommendation Adopted:`.

**51 of 51 items carry a recorded action.** Dispositions for 30 June 2026:

| Disposition | Count |
|---|---|
| adopted | 45 |
| other | 5 |
| continued | 1 |

Every flagged item resolves to an outcome with a page citation into the
Annotated Agenda:

| Item | Outcome |
|---|---|
| 1 parking meters | Adopted — Ordinance 8,012-N.S. (p.3) |
| 2 library relief tax | Adopted — Ordinance 8,013-N.S. (p.3) |
| 3 library services tax | Adopted — Ordinance 8,014-N.S. (p.3) |
| 12 parks and street trees | Adopted — Ordinance 8,023-N.S. (p.6) |
| 14 SAFE STREETS | Adopted — Ordinance 8,025-N.S. (p.7) |
| 46 surveillance policy | Adopted — Resolution 72,369-N.S. (p.19), 17 speakers |

### The ledger's final column
Item 46 was adopted **"as presented in the item from the City Manager"**, moved
by Blackaby/Humbert after 17 speakers. So the chain completes:

> the committee asked for a process to notify camera owners when their footage
> is accessed → the department returned a non-binding feasibility question to
> vendors, explicitly not a requirement → the council adopted it as presented.

The provision did not survive, and the record says so at a specific page.

### An unfinished lineage
Item 45 (rent stabilisation initiative) was **continued to 7 July 2026**,
"including revised material in Supplemental Communications". This is the
continued-to-a-date-certain case: the decision is still travelling, and its next
version will carry different revised material. It is the natural next lineage to
track.

---

## 11. Deployment readiness

Not yet deployed — deliberately, to avoid idle spend. Findings from the dry run:

- **The Python starter toolkit is deprecated.** `bedrock-agentcore-starter-toolkit`
  now prints a deprecation notice and its `deploy --help` crashes. AWS directs
  users to the AgentCore CLI (`npm install -g @aws/agentcore`, v0.28.1 here).
- **No container runtime is required.** The CLI's default build type is
  **CodeZip**, not Container, so Docker/Finch/Podman are unnecessary. Deployment
  is CDK-based, with `--dry-run` and `--diff` available before spending.
- Scaffolded config validates (`agentcore validate` → `Valid`) with a CodeZip
  runtime on Python 3.14 and a memory declaring **SEMANTIC**, **USER_PREFERENCE**
  and **SUMMARIZATION** strategies.
- The remaining gate is CDK bootstrap, which is what starts billing.

### Teardown exists before deployment, not after
`scripts/teardown.py` sweeps runtimes, browsers, code interpreters, memories and
gateways. Dry run by default; `--yes` deletes. AWS-managed defaults
(`aws.browser.*`, `aws.codeinterpreter.*`) are skipped — they cannot be deleted
and cost nothing.

Idle compute is the expensive failure mode, not active compute: a runtime left
alive bills continuously while a full pipeline run costs about two cents.

---

## 12. Making the package deployable

The pipeline modules originally resolved their data by walking up the source
tree (`Path(__file__).parents[2]`). That works from a checkout and breaks the
moment the package is installed or zipped into a runtime — the cache directory,
the household profile and the Cedar policy would all have been missing.

`src/quorum/paths.py` now resolves each location in a fixed order:

1. an environment variable — `QUORUM_CACHE_DIR`, `QUORUM_PROFILE`, `QUORUM_POLICY`
2. data bundled inside the installed package
3. the repository checkout

The cache falls back to a temp directory when its target is unwritable, so a
read-only deployment still runs. The policy does **not** fall back: if no Cedar
policy can be found, it raises. An action gate that cannot load its policy must
fail closed, not open.

The Cedar policy and default profile are bundled into the wheel via hatch
`force-include`, so an installed copy enforces policy with no checkout present.

### One source of truth for the deployed agent
AgentCore CodeZip packages only `codeLocation` (`deploy/app/quorumAgent/`), so
the pipeline would have had to be copied in. Instead the deployed app declares
a dependency on the package itself:

    "quorum @ git+https://github.com/TusharTechs/quorum-civic-agent@main"

No duplicated source, and the deployed agent runs exactly the code in this
repository.

**This makes the repository a build dependency of its own deployment.** The
root `pyproject.toml` must be pushed to `main` before `agentcore deploy` will
resolve.

### The deployed agent
`deploy/app/quorumAgent/skills/quorum_tools.py` exposes four tools:

| Tool | Does |
|---|---|
| `analyse_packet` | runs the whole Graph, returns decisions with page citations and the run's token usage |
| `track_decision` | resolves one decision across several meetings despite renumbering |
| `verify_outcome` | reads the Annotated Agenda and reports what the council actually did |
| `prepare_comment` | drafts, verifies grounding, asks Cedar — and never files |

The system prompt states the constraints the code enforces: lead with the
decision, cite every claim, say plainly when nothing is relevant, never call the
output an AI summary, and report the policy engine's refusal exactly as given.

Verified locally: all four tools load, `agentcore validate` returns `Valid`, and
the existing pipeline regressions still pass after the path refactor.

---

## 13. Household cost, and why the model is not allowed to do the arithmetic

`src/quorum/cost.py` classifies every rate item on an agenda and totals what it
costs one household. Classification, not arithmetic, is the hard part — a single
agenda phrases three different bases almost identically.

Result for 30 June 2026, a 1,450 sq ft dwelling assessed at $1.2M:

```
per square foot of dwelling   $1.11167/sqft   x 1,450      = $1,611.92
percent of assessed value     0.0490%         x $1,200,000 =   $588.00
                                                             ----------
                                                             $2,199.92
```

across **13 separate agenda items**. Every rate carries the item number, packet
page and ordinance number it was read from, so a wrong figure is traceable
rather than merely wrong.

Two rates are excluded and both look like household rates:
- item 4, `$0.9168 per square foot of improvements` — **large non-profits only**
- item 20, a per-trip tax on ride-hailing — not levied on property

A naive sum of everything matching "per square foot" gives **$3,529.28**,
overstating this household by **$1,329.36 a year**.

### Evidence that the model should not compute this
Before the figures were computed in code, the drafting model was asked to
consolidate the tax items itself. It reported the per-square-foot total as
**$0.89/sq ft** against a true **$1.11167**. It was not obviously wrong on the
page — it read like a confident, specific number.

The arithmetic is therefore done in Python and handed to the model as
established fact, with the instruction to use the figures verbatim and not
re-derive them. The model's job is to explain a number, not to produce one.
Verified: the alert now states $2,199.92, matching the code exactly.

### A deterministic floor beneath model triage
Model triage recall varied between runs on identical input (5, 16, 12, 8, 15
candidates across runs), and in one run dropped item 7 — a tax the household
actually pays.

Rate-bearing items now **bypass triage entirely**: any item whose recommendation
classifies as a dwelling or assessed-value rate is always a candidate. A tax
levied on this household's home affects it whether or not a model notices.

In the verified run the filter added items 13 and 15, which triage had missed,
and all 13 tax items reached the alert. The model still makes the judgement
calls — parking, ballot measures, zoning — it simply gets no vote on facts
already established in code.

This closes the largest known quality risk recorded in section 9.

---

## 14. The product surface

`src/quorum/report.py` renders a completed run as a **single self-contained HTML
file** — no external requests, no fonts, no scripts. It opens from disk, renders
on a machine with no network, and survives being emailed. 17 KB.

Nothing on the page is sample data. Every figure, quote and page link is
produced by the run that generated it; if a value is not in the run, the section
does not appear. The page is generated by `scripts/build_report.py`, which runs
the real Graph against the real packet before rendering.

Sections, in the order a reader needs them:

1. **"Why QUORUM interrupted you"** — the heading is the product claim. It is
   never "AI summary": an interruption has to be earned and the page answers
   for it.
2. **Attention efficiency** — `1,790 pages → 51 items → 15 candidates →
   3 decisions`, stated as a single line at the top.
3. **Decision cards** — WHAT / WHY YOU / WHY NOW / EVIDENCE, with the packet
   quoted verbatim and a deep link to the exact page.
4. **What this meeting costs this household** — every rate with its item, page
   and ordinance number, the excluded rates shown greyed with the reason they
   are excluded, and the naive total alongside the correct one.
5. **The comment prepared, and not sent** — the Cedar refusal, with the
   grounding check shown passing beside it, so it is unmistakable that the
   comment was blocked on standing rather than on quality.
6. **What the council actually did** — outcomes read from the Annotated Agenda,
   each linking to its page.

Renders in light and dark, and reflows on a narrow viewport. Verified in a
browser rather than assumed.

The generated file is gitignored: it is output, and it embeds a timestamp, so
committing it would produce noise on every run.
