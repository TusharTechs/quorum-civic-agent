# QUORUM — demo video plan

Five minutes, hard limit. Every beat below is backed by something that already
runs; nothing here needs to be built first. Figures are the verified ones from
`engineering-log.md` — do not round them on screen, the precision is the point.

**The memorable moment is not "an agent found something." It is "the agent came
back."** Everything is arranged to reach the demoted provision at 2:20.

---

## What must exist before recording

| Asset | Status | Command |
|---|---|---|
| Report page | ready | `python scripts/build_report.py` → `data/report.html` |
| Full pipeline run | ready | `python scripts/run_graph.py` |
| Lineage + diff | ready | `python scripts/build_lineages.py` |
| Cost with provenance | ready | `python scripts/household_cost.py` |
| Interrupt → Cedar refusal | ready | `python scripts/run_action.py` |
| Outcome verification | ready | `python scripts/verify_outcomes.py` |
| AgentCore live | **redeploy on the day** | `cd deploy && agentcore deploy --yes` |
| Teardown after filming | — | delete the CloudFormation stack |

Open in tabs beforehand: the 7 May packet, the 30 June packet, the Annotated
Agenda, `report.html`, the AgentCore console, and a terminal.

---

## Beat sheet

### 0:00–0:15 — the scale, in silence
Screen: scroll fast through the real 30 June packet. Page counter climbing.

> "Berkeley published this last Tuesday. One thousand, seven hundred and ninety
> pages. It was online for six days before the vote."

No music over the number. Let the scroll bar do the work.

### 0:15–0:35 — the problem, and one household
Screen: the household profile, then the packet again.

> "Somewhere in there are the decisions that touch a specific house on Hopkins
> Street. The people who used to read this for you — local reporters — mostly
> don't exist any more. Public comment opens and closes with almost nobody
> informed enough to use it."

### 0:35–0:55 — it already ran
Screen: `report.html` at the top. The funnel line.

> "QUORUM read all of it overnight. Nobody asked it to."

Point at the line: **1,790 pages → 51 agenda items → 15 candidates →
3 decisions.** Then say the cost out loud:

> "Two cents. And when nothing on the agenda affects you, it says so and spends
> nothing at all."

### 0:55–1:25 — why you were interrupted
Screen: the first decision card.

Read WHAT / WHY YOU / WHY NOW. Then click the evidence link and land on
**page 4 of the real PDF**. Let the browser load the actual document.

> "Every claim is a link. You can check it."

### 1:25–2:05 — the number nobody computes
Screen: the cost table.

> "Thirteen separate agenda items set a tax on this house. No single document
> adds them up. This one does: **two thousand, one hundred and ninety-nine
> dollars and ninety-two cents** a year."

Then the trap — point at the greyed row:

> "This rate is the biggest one on the page and it's phrased identically to the
> others. It applies only to large non-profits. Include it and you overstate
> this household by one thousand three hundred and twenty-nine dollars. QUORUM
> does the arithmetic in code, not in the model — because when we let the model
> do it, it got it wrong, confidently."

### 2:05–3:00 — THE CENTREPIECE: the provision that was quietly demoted
Screen: two PDFs side by side, May and June.

> "In May, Berkeley's Public Safety Committee reviewed a police surveillance
> policy and asked for eleven specific changes. One of them was simple: tell
> camera owners when police access their footage."

Search the 7 May packet for `repositioned to capture an area` — **no results**.
Search the 30 June packet — **four hits**. Show the diff output: six substantive
additions, including a First Amendment protection and a 72-hour notification if
a federal agency is given camera data.

Then page 1394, and read it verbatim:

> "*The Department will include in the RFP a request for vendors to describe the
> feasibility of notifying camera owners each time BPD personnel access their
> feed. **This is not a minimum requirement for vendor selection.***"

Beat. Then:

> "They asked for a process. What they got was an optional question to vendors.
> The provision wasn't deleted — it was demoted. Anyone skimming the response
> would think the request was granted."

Then the outcome, from the Annotated Agenda, page 19:

> "Adopted as presented. Seventeen speakers. Resolution 72,369."

> "That's the whole product. Not 'here's a summary' — **here's what you asked
> for, and here's what happened to it.**"

### 3:00–3:35 — bounded autonomy
Screen: terminal running `run_action.py`.

Draft appears, grounding check passes 2/2 quotes verified, zero uncited claims.
Interrupt fires. Approve it — ideally from a phone.

> "That approval resumed a tool call in a different process. The agent had
> already exited."

Then Cedar refuses:

> "⛔ Blocked. The identity has no standing in this jurisdiction. I'm in India.
> Filing a comment into a Berkeley meeting on an item I have no stake in is
> astroturfing — which is exactly what this policy exists to prevent."

> "**The model can recommend an action. It cannot grant itself permission to
> take one — including when the operator is me.**"

### 3:35–4:00 — it doesn't cry wolf
Screen: the archive path.

> "Same pipeline, a week where nothing lands on your street. No action
> recommended. Fifty-one items archived, zero model calls, zero cost. Most
> civic tech maximises engagement. This maximises the value of an
> interruption."

### 4:00–4:35 — the architecture, briefly
Screen: the Graph diagram, then the AgentCore console with the live runtime.

> "Strands Graph as the lifecycle coordinator — conditional edges, a real error
> edge that halts when a packet can't be parsed rather than guessing. Cheap
> model over everything, expensive model over the few that survive. Identity
> resolution across meetings is deterministic, never a model, because identity
> has to be auditable. Cedar enforces the action policy outside agent code.
> Running on AgentCore Runtime with Memory."

Show the deployed agent answering the outcome question live.

### 4:35–5:00 — close
Screen: back to `report.html`.

> "One thousand seven hundred and ninety pages. Three decisions. One of them
> was a provision that quietly disappeared between two meetings, and now
> somebody knows."

> "**Your city has a memory. Now you do too.**"

---

## Rules for the take

- **Say the numbers precisely.** $2,199.92, not "about two thousand". Precision
  is the evidence that this is real.
- **Click through to at least two real PDFs on camera.** The verifiability is
  the moat; a judge who pauses and checks should find it correct.
- **Do not say "autonomous civic intelligence agent"** in the first four
  minutes. Earn the abstraction.
- **Never say "AI summary."**
- Don't apologise for the refusal beat — it is the strongest thirty seconds in
  the video, not a limitation.
- If a take runs long, cut the architecture beat before cutting the demotion.

## Things NOT to claim
- Do not claim OCR works. The error edge halts; it does not yet OCR.
- Do not claim general jurisdiction coverage. One city, deeply, is the honest
  claim; special-meeting packets do not segment yet.
- Do not imply a comment was ever filed. Nothing has been filed, by design.
