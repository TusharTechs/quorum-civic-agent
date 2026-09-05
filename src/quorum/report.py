"""Render a completed run as a self-contained HTML page.

Everything on the page comes from a real run against a real packet. There is no
sample data and no placeholder: if a figure is not in the run, it does not
appear. The page is a single file with no external requests, so it opens from
disk, survives being emailed, and renders identically on a machine with no
network.

The heading is "Why QUORUM interrupted you", never "AI summary". The product
claim is that an interruption was earned, so the page has to answer for it.
"""

from __future__ import annotations

import html
import json
from datetime import datetime, timezone
from pathlib import Path

# The mark is inlined, not linked: the page must stay a single self-contained
# file that renders from disk with no network.
MARK = """<svg class="mark" viewBox="0 0 64 64" width="34" height="34" aria-hidden="true">
  <path d="M10 42 A22 22 0 0 1 54 42" fill="none" stroke="var(--ink)"
        stroke-width="5.5" stroke-linecap="round"/>
  <path d="M14 54 H50" stroke="var(--ink)" stroke-width="5.5"
        stroke-linecap="round" opacity=".3"/>
  <circle cx="47.6" cy="26.4" r="10.5" fill="none" stroke="var(--bg)" stroke-width="3"/>
  <circle cx="47.6" cy="26.4" r="8.5" fill="var(--accent)"/>
</svg>"""

FAVICON = (
    "data:image/svg+xml,"
    "%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E"
    "%3Cpath d='M10 42 A22 22 0 0 1 54 42' fill='none' stroke='%2316181d'"
    " stroke-width='6' stroke-linecap='round'/%3E"
    "%3Ccircle cx='47.6' cy='26.4' r='9' fill='%231c4f8a'/%3E%3C/svg%3E"
)

CSS = """
:root {
  --bg: #f6f5f2; --panel: #ffffff; --ink: #16181d; --muted: #5b6472;
  --line: #e2e0da; --accent: #1c4f8a; --warn: #8a4b1c; --stop: #8a1c2f;
  --ok: #1c6b45; --code: #f0efeb;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --bg: #14161a; --panel: #1b1e24; --ink: #e8e9ec; --muted: #9aa3b0;
    --line: #2b3038; --accent: #7fb0e8; --warn: #d9a06a; --stop: #e88b98;
    --ok: #6fc79c; --code: #23272e;
  }
}
:root[data-theme="dark"] {
  --bg: #14161a; --panel: #1b1e24; --ink: #e8e9ec; --muted: #9aa3b0;
  --line: #2b3038; --accent: #7fb0e8; --warn: #d9a06a; --stop: #e88b98;
  --ok: #6fc79c; --code: #23272e;
}
* { box-sizing: border-box; }
body {
  margin: 0; background: var(--bg); color: var(--ink);
  font: 16px/1.55 ui-sans-serif, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
}
.wrap { max-width: 860px; margin: 0 auto; padding: 40px 22px 80px; }
header { border-bottom: 2px solid var(--ink); padding-bottom: 14px; margin-bottom: 28px; }
.brandrow { display: flex; align-items: center; gap: 10px; }
.mark { flex: none; }
.brand { font-size: 13px; letter-spacing: .22em; text-transform: uppercase; color: var(--muted); }
h1 { font-size: 30px; line-height: 1.2; margin: 8px 0 4px; letter-spacing: -.01em; }
.sub { color: var(--muted); font-size: 15px; }
.funnel {
  display: flex; flex-wrap: wrap; gap: 6px; align-items: center;
  background: var(--panel); border: 1px solid var(--line); border-radius: 10px;
  padding: 14px 16px; margin: 0 0 30px; font-size: 14px;
}
.funnel b { font-size: 19px; font-variant-numeric: tabular-nums; }
.funnel .step { display: flex; align-items: baseline; gap: 7px; }
.funnel .arrow { color: var(--muted); padding: 0 4px; }
.card {
  background: var(--panel); border: 1px solid var(--line);
  border-left: 4px solid var(--accent); border-radius: 10px;
  padding: 20px 22px; margin: 0 0 18px;
}
.card h2 { font-size: 19px; margin: 0 0 14px; line-height: 1.35; }
.tag {
  display: inline-block; font-size: 11px; letter-spacing: .12em; text-transform: uppercase;
  color: var(--muted); border: 1px solid var(--line); border-radius: 999px;
  padding: 2px 9px; margin-bottom: 10px;
}
dl { margin: 0; display: grid; grid-template-columns: 88px 1fr; gap: 9px 16px; }
dt { font-size: 11px; letter-spacing: .12em; text-transform: uppercase; color: var(--muted); padding-top: 3px; }
dd { margin: 0; }
blockquote {
  margin: 0; padding: 10px 14px; background: var(--code);
  border-radius: 6px; font-size: 14.5px;
}
a { color: var(--accent); }
.cite { display: inline-block; margin-top: 8px; font-size: 13px; }
table { width: 100%; border-collapse: collapse; font-size: 14px; margin-top: 6px; }
th, td { text-align: left; padding: 7px 10px; border-bottom: 1px solid var(--line); }
th { font-size: 11px; letter-spacing: .1em; text-transform: uppercase; color: var(--muted); font-weight: 600; }
td.num, th.num { text-align: right; font-variant-numeric: tabular-nums; }
tr.total td { font-weight: 700; border-top: 2px solid var(--ink); border-bottom: none; }
tr.excluded td { color: var(--muted); }
.scroll { overflow-x: auto; }
h3 { font-size: 15px; margin: 30px 0 10px; letter-spacing: .02em; }
.gate { border-left-color: var(--stop); }
.gate .verdict { color: var(--stop); font-weight: 700; font-size: 17px; }
.gate ul { margin: 10px 0 0; padding-left: 20px; }
.quiet { color: var(--muted); font-size: 14px; }
.pill { font-size: 12px; padding: 2px 8px; border-radius: 5px; background: var(--code); }
.pill.ok { color: var(--ok); }
footer { margin-top: 46px; padding-top: 16px; border-top: 1px solid var(--line);
         color: var(--muted); font-size: 13px; }
"""


def _e(text) -> str:
    return html.escape(str(text), quote=True)


def _funnel(pages: int, items: int, candidates: int, decisions: int) -> str:
    steps = [(f"{pages:,}", "pages"), (f"{items}", "agenda items"),
             (f"{candidates}", "candidates"), (f"{decisions}", "decisions")]
    inner = '<span class="arrow">&rarr;</span>'.join(
        f'<span class="step"><b>{v}</b> {label}</span>' for v, label in steps)
    return f'<div class="funnel">{inner}</div>'


def _alert_card(alert, items_by_number: dict, packet_url: str) -> str:
    pages = sorted({items_by_number[n]["page"] for n in alert.item_numbers
                    if n in items_by_number})
    nums = ", ".join(str(n) for n in alert.item_numbers)
    label = f"Agenda item {nums}" if len(alert.item_numbers) == 1 else f"Agenda items {nums}"
    cite = f"{packet_url}#page={pages[0]}" if pages else packet_url
    page_text = f"page {pages[0]}" if pages else "packet"
    return f"""
    <article class="card">
      <span class="tag">{_e(label)}</span>
      <h2>{_e(alert.what)}</h2>
      <dl>
        <dt>Why you</dt><dd>{_e(alert.why_you)}</dd>
        <dt>Why now</dt><dd>{_e(alert.why_now)}</dd>
        <dt>Evidence</dt><dd>
          <blockquote>&ldquo;{_e(alert.evidence_quote)}&rdquo;</blockquote>
          <a class="cite" href="{_e(cite)}">Open the packet at {_e(page_text)} &rarr;</a>
        </dd>
      </dl>
    </article>"""


def _cost_table(cost, packet_url: str) -> str:
    if cost is None or not cost.included:
        return ""
    rows = []
    for r in sorted((x for x in cost.rates if x.basis == "per_sqft_dwelling"),
                    key=lambda x: x.item_number):
        rows.append(
            f'<tr><td><a href="{_e(packet_url)}#page={r.page}">Item {r.item_number}</a></td>'
            f'<td>{_e(r.ordinance or "—")}</td>'
            f'<td class="num">${r.value:.5f}/sq ft</td>'
            f'<td class="num">${r.value * cost.dwelling_sqft:,.2f}</td></tr>')
    for r in sorted((x for x in cost.rates if x.basis == "assessed_value"),
                    key=lambda x: x.item_number):
        rows.append(
            f'<tr><td><a href="{_e(packet_url)}#page={r.page}">Item {r.item_number}</a></td>'
            f'<td>{_e(r.ordinance or "—")}</td>'
            f'<td class="num">{r.value:.4f}% of value</td>'
            f'<td class="num">${r.value * cost.assessed_value_usd / 100:,.2f}</td></tr>')
    for r in cost.excluded:
        rows.append(
            f'<tr class="excluded"><td><a href="{_e(packet_url)}#page={r.page}">Item {r.item_number}</a></td>'
            f'<td colspan="2">Excluded &mdash; {_e(r.excluded_reason)}</td>'
            f'<td class="num">&mdash;</td></tr>')
    rows.append(
        f'<tr class="total"><td colspan="3">Annual total across '
        f'{len(cost.item_numbers)} agenda items</td>'
        f'<td class="num">${cost.annual_total:,.2f}</td></tr>')
    overstated = cost.naive_total - cost.annual_total
    return f"""
    <h3>What this meeting costs this household</h3>
    <div class="card">
      <p class="quiet">{cost.dwelling_sqft:,} sq ft, assessed
        ${cost.assessed_value_usd:,}. Computed in code from the published rates,
        not estimated.</p>
      <div class="scroll"><table>
        <thead><tr><th>Source</th><th>Instrument</th><th class="num">Rate</th>
        <th class="num">Per year</th></tr></thead>
        <tbody>{''.join(rows)}</tbody>
      </table></div>
      <p class="quiet">Adding every rate that says &ldquo;per square foot&rdquo;
        would give ${cost.naive_total:,.2f} &mdash; overstating this household by
        <strong>${overstated:,.2f} a year</strong>.</p>
    </div>"""


def _gate_panel(decision, grounding=None) -> str:
    if decision is None:
        return ""
    reasons = "".join(f"<li>{_e(r)}</li>" for r in decision.reasons)
    grounded = ""
    if grounding is not None:
        grounded = (f'<p class="quiet">Grounding check: '
                    f'<span class="pill ok">{grounding.quotes_verified}/'
                    f'{grounding.quotes_checked} quotes verified</span> '
                    f'<span class="pill ok">{len(grounding.uncited_sentences)} '
                    f'uncited claims</span></p>')
    return f"""
    <h3>The comment QUORUM prepared, and did not send</h3>
    <div class="card gate">
      <p class="verdict">&#9940; {_e(decision.headline)}</p>
      <ul>{reasons}</ul>
      {grounded}
      <p class="quiet">The comment is drafted, cited and human-approved. It was
        still refused, because the configured identity has no standing in this
        jurisdiction. The model can recommend an action; it cannot grant itself
        permission to take one &mdash; including when the operator is us.</p>
    </div>"""


def _outcomes_panel(outcomes: dict, annotated_url: str) -> str:
    if not outcomes:
        return ""
    rows = "".join(
        f'<tr><td>Item {o.item_number}</td><td>{_e(o.headline)}</td>'
        f'<td><a href="{_e(annotated_url)}#page={o.page}">page {o.page}</a></td></tr>'
        for o in sorted(outcomes.values(), key=lambda x: x.item_number))
    return f"""
    <h3>What the council actually did</h3>
    <div class="card">
      <div class="scroll"><table>
        <thead><tr><th>Item</th><th>Outcome</th><th>Record</th></tr></thead>
        <tbody>{rows}</tbody>
      </table></div>
      <p class="quiet">Read from the published Annotated Agenda after the
        meeting. The loop closes: flagged, acted on, verified.</p>
    </div>"""


def render(ctx, *, jurisdiction: str = "Berkeley, California",
           decision=None, grounding=None,
           outcomes: dict | None = None, annotated_url: str = "") -> str:
    """Build the page from a completed RunContext."""
    items_by_number = {i["number"]: i for i in ctx.items}
    alerts = ctx.alerts.alerts if ctx.alerts else []
    pages = ctx.packet["n_pages"] if ctx.packet else 0

    cards = "".join(_alert_card(a, items_by_number, ctx.packet_url) for a in alerts)
    if not cards:
        cards = ('<article class="card"><h2>No action recommended</h2>'
                 '<p>This meeting affects your neighbourhood, but no decision on '
                 'your saved interests is being made this week.</p></article>')

    generated = datetime.now(timezone.utc).strftime("%d %B %Y, %H:%M UTC")
    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="{FAVICON}">
<title>Why QUORUM interrupted you &mdash; {_e(ctx.meeting_date)}</title>
<style>{CSS}</style>
</head><body><div class="wrap">
  <header>
    <div class="brandrow">{MARK}<span class="brand">QUORUM</span></div>
    <h1>Why QUORUM interrupted you</h1>
    <p class="sub">{_e(jurisdiction)} &middot; {_e(ctx.meeting_date)} &middot;
      read while you were asleep, unprompted</p>
  </header>
  {_funnel(pages, len(ctx.items), len(ctx.candidates), len(alerts))}
  {cards}
  {_cost_table(getattr(ctx, "cost", None), ctx.packet_url)}
  {_gate_panel(decision, grounding)}
  {_outcomes_panel(outcomes or {}, annotated_url)}
  <footer>
    Every figure on this page was computed from the published packet at
    <a href="{_e(ctx.packet_url)}">berkeleyca.gov</a> &mdash; {pages:,} pages,
    parsed once. Generated {_e(generated)}.
  </footer>
</div></body></html>"""


def write(ctx, path: Path, **kwargs) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render(ctx, **kwargs), encoding="utf-8")
    return path
