# QUORUM

> Your city publishes hundreds of pages a week. QUORUM reads all of it, and
> tells you the one paragraph that lands on your street.

**Your city has a memory. Now you do too.**

Berkeley City Council's agenda packet for 30 June 2026 is **1,790 pages**. It was
published with days of notice. It contains eleven separate tax rates that apply to
your home, a parking ordinance that changes your street, and a police surveillance
policy that was quietly rewritten since May.

Almost nobody reads it. QUORUM does, every week, unprompted.

---

## What it actually found

QUORUM tracked one decision across two published packets, two months apart.

In May, Berkeley's Public Safety Policy Committee reviewed a police surveillance
use policy and asked for **eleven specific revisions**. One of them:

> *"Develop a process for notifying camera owners when their camera footage is
> accessed."*

In the 30 June packet, the department's response reads:

> *"the Department will include in the RFP a request for vendors to describe the
> **feasibility** of notifying camera owners each time BPD personnel access their
> feed. **This is not a minimum requirement for vendor selection** but will be
> evaluated as a value-added feature..."*

The committee asked for a **process**. What appeared was a **feasibility question
to vendors, explicitly not required**. The provision was not deleted — it was
quietly demoted. Someone skimming the response would believe the request was
granted.

QUORUM also verified what *was* added — six substantive new safeguards, including
a First Amendment protection barring the monitoring of lawful protests, and a
72-hour notification requirement if a federal agency is given camera data.

### Verify it yourself in ninety seconds

1. Open the [7 May 2026 packet](https://berkeleyca.gov/sites/default/files/city-council-meetings/2026-05-07%20Revised%20Special%20Agenda%20Packet%20-%20Council%20-%20WEB.pdf) (176 pages) and search for
   `repositioned to capture an area`. **Not there.**
2. Open the [30 June 2026 packet](https://berkeleyca.gov/sites/default/files/city-council-meetings/2026-06-30%20Agenda%20Packet%20-%20Council%20-%20WEB.pdf) (1,790 pages) and search the same
   string. **Pages 1395, 1402, 1413, 1415.**

No mocks. No synthetic data. No API. Two public PDFs and a diff.

---

## Attention efficiency

On the real 30 June packet, one run:

```
1,790 pages  ->  51 agenda items  ->  12 candidates  ->  3 decisions
```

Cost per full run: **$0.02**. When nothing on the agenda affects the household,
QUORUM says *"no action recommended"* and spends **$0.00** — no model is called
at all.

---

## The bit most agents skip: it cannot act on its own

QUORUM drafts public comments. It cannot file one.

Every submission passes through a [Cedar policy](policy/quorum.cedar) evaluated by
the **real Cedar engine**, outside agent code:

- a human must approve, and the approval must be under 24 hours old
- every factual assertion must be traceable to a cited packet page
- one comment per meeting, one verified identity
- **the identity must have standing in that jurisdiction**

That last rule refuses this project's own author. QUORUM is built from India;
filing a comment into a Berkeley meeting on an item its operator has no stake in
*is astroturfing*. So the demo shows the policy engine blocking its own author:

```
DRAFT      3 verbatim quotes, all cited (packet p.3)
GROUNDING  3/3 quotes verified, 0 uncited claims
INTERRUPT  "Approve filing this comment into the public record?"
APPROVED   resumed mid-tool, in a different OS process
CEDAR      BLOCKED - no verified standing in this jurisdiction
OUTCOME    comment prepared, not filed
```

> **The LLM can recommend an action. It cannot grant itself permission to take
> it — including when the operator is us.**

---

## Architecture

Built on the [Strands Agents SDK](https://strandsagents.com). The `Graph` is the
lifecycle coordinator; there is no supervisor agent layered on top of it.

```
watch -> ingest -> segment -> triage --(candidates)--> deep_read -> diff -> draft
                      |            \                                        |
                (unparseable)   (nothing relevant)              <INTERRUPT: approval>
                      |                  |                                  |
                      v                  v                          Cedar policy gate
                 ocr_fallback        archive                                |
            "evidence incomplete"  "no action                        file / refuse
                                    recommended"                            |
                                                                     verify in record
```

Deterministic work — fetching, parsing, segmenting, diffing, grounding checks —
runs as `MultiAgentBase` nodes. It costs nothing and is auditable. Models are used
only where reasoning is required, routed by cost: **Nova Lite** for triage over
every item, **Claude Sonnet 4.5** for the handful that survive.

Identity resolution across meetings is deterministic too — matched on BMC section
and ordinance number, never by an LLM — because identity must be auditable. The
same ordinance appears as item 14 with no number in March and as item 1,
*Ordinance 8,003-N.S.*, two weeks later. In the first-reading packet its heading
is literally `ORDINANCE NO. -N.S.` — the decision has no identity until it passes.

| Module | Role |
|---|---|
| [`ingest.py`](src/quorum/ingest.py) | Fetch and parse packets once, ever. Provenance on every page. |
| [`segment.py`](src/quorum/segment.py) | Structural segmentation into agenda items. No LLM. |
| [`stake.py`](src/quorum/stake.py) | Triage and decision-level alerts: WHAT / WHY YOU / WHY NOW / EVIDENCE |
| [`lineage.py`](src/quorum/lineage.py) | Cross-meeting entity resolution, enacting-text diff, vote extraction |
| [`action.py`](src/quorum/action.py) | Draft, grounding verification, interrupt, policy gate |
| [`policy.py`](src/quorum/policy.py) | Cedar evaluation |
| [`pipeline.py`](src/quorum/pipeline.py) | The Strands `Graph` |

---

## Running it

```bash
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt
aws configure                                       # region us-west-2
python scripts/run_graph.py                         # full pipeline on a real packet
python scripts/build_lineages.py                    # cross-meeting lineages
python scripts/run_action.py                        # draft -> interrupt -> policy gate
```

Requires Bedrock access to `us.anthropic.claude-sonnet-4-5-*` and
`us.amazon.nova-lite-v1:0` in `us-west-2`.

---

## Honest limitations

- Triage recall varies between runs; a deterministic pre-filter for rate and fee
  items is the planned fix. This is what the evaluation harness measures.
- Special-meeting packets number items `1a`/`1b` and are not yet segmented.
- The OCR fallback edge is wired and fires correctly, but does not yet OCR — it
  refuses to proceed rather than reasoning over text it cannot verify.

---

## Licence

MIT — see [LICENSE](LICENSE).
