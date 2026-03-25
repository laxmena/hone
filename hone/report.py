import json
import math
import html as html_lib
from pathlib import Path
from . import Config

def _is_error_score(score):
    try:
        return math.isinf(score) or math.isnan(score) or score >= 999
    except (TypeError, ValueError):
        return True

def _fmt_score(score):
    if _is_error_score(score):
        return "Error"
    return str(score)

class Report:
    def __init__(self, config: Config):
        self.dir = config.workspace / ".hone" / "runs" / config.run_id
        self.json_path = self.dir / "run.json"
        self.html_path = self.dir / "report.html"

    def generate(self):
        if not self.json_path.exists():
            return

        data = json.loads(self.json_path.read_text())
        config = data.get("config", {})
        iterations = data.get("iterations", [])
        baseline = data.get("baseline", {}).get("score", None)
        best_score = data.get("best_score", None)
        final_cost = data.get("final_cost", 0)
        final_tokens = data.get("final_tokens", 0)
        optimize = config.get("optimize", "lower")
        target = config.get("target")

        # improvement
        if baseline and best_score:
            if optimize == "lower" and baseline > 0:
                improvement = (baseline - best_score) / baseline * 100
                improvement_label = f"{improvement:.1f}% faster"
            elif baseline > 0:
                improvement = (best_score - baseline) / baseline * 100
                improvement_label = f"{improvement:.1f}% better"
            else:
                improvement_label = "N/A"
        else:
            improvement_label = "N/A"

        # chart data — replace error sentinel values with null so Chart.js skips them
        chart_labels = [str(it["n"]) for it in iterations]
        chart_scores = [None if _is_error_score(it["score"]) else it["score"] for it in iterations]
        chart_accepted = [it["accepted"] for it in iterations]
        chart_error = [_is_error_score(it["score"]) for it in iterations]
        chart_labels_js = json.dumps(chart_labels)
        chart_scores_js = json.dumps(chart_scores)
        chart_colors_js = json.dumps([
            "#94a3b8" if err else ("#22c55e" if acc else "#ef4444")
            for err, acc in zip(chart_error, chart_accepted)
        ])

        baseline_line = f", {{label:'Baseline',data:Array({len(iterations)}).fill({baseline}),borderColor:'#94a3b8',borderDash:[6,3],pointRadius:0,borderWidth:1.5,fill:false}}" if baseline is not None else ""
        target_line = f", {{label:'Target',data:Array({len(iterations)}).fill({target}),borderColor:'#f59e0b',borderDash:[4,4],pointRadius:0,borderWidth:1.5,fill:false}}" if target is not None else ""

        # iteration cards
        cards_html = ""
        for it in iterations:
            accepted = it["accepted"]
            is_err = _is_error_score(it["score"])
            score_display = _fmt_score(it["score"])

            if is_err:
                badge_cls, badge_text = "badge-error", "Error"
                card_cls = "card-error"
            elif accepted:
                badge_cls, badge_text = "badge-accepted", "Accepted"
                card_cls = "card-accepted"
            else:
                badge_cls, badge_text = "badge-reverted", "Reverted"
                card_cls = "card-reverted"

            reasoning = html_lib.escape(it.get("reasoning", ""))
            stdout = html_lib.escape(it.get("stdout", "").strip())
            violations = it.get("violations", [])
            violations_html = ""
            if violations:
                v_items = "".join(f"<li>{html_lib.escape(v)}</li>" for v in violations)
                violations_html = f'<div class="violations"><strong>Constraint violations:</strong><ul>{v_items}</ul></div>'

            ops_html = ""
            for op in it.get("operations", []):
                op_type = op.get("type", "write")
                op_path = html_lib.escape(op.get("path", ""))
                content = html_lib.escape(op.get("content", ""))
                ops_html += f"""
                <div class="op-block">
                    <div class="op-header"><span class="op-type">{op_type}</span> {op_path}</div>
                    <pre class="code-block"><code>{content}</code></pre>
                </div>"""

            stdout_summary = "Benchmark output" if not is_err else "Benchmark output (failed)"
            stdout_block = f"""
            <details class="stdout-details" {'open' if is_err else ''}>
                <summary>{stdout_summary}</summary>
                <pre class="stdout-block {'stdout-error' if is_err else ''}">{stdout}</pre>
            </details>""" if stdout else ""

            ops_block = f"""
            <details class="ops-details">
                <summary>Code changes ({len(it.get('operations', []))} file(s))</summary>
                {ops_html}
            </details>""" if it.get("operations") else ""

            score_cell = f'<div class="iter-score">Score: <strong class="{"score-error" if is_err else ""}">{score_display}</strong></div>'

            cards_html += f"""
            <div class="iter-card {card_cls}">
                <div class="iter-header">
                    <div class="iter-title">
                        <span class="iter-num">Iteration {it['n']}</span>
                        <span class="badge {badge_cls}">{badge_text}</span>
                    </div>
                    {score_cell}
                </div>
                <div class="hypothesis-block">
                    <span class="hypothesis-label">Hypothesis</span>
                    <p class="reasoning">{reasoning}</p>
                </div>
                {violations_html}
                <div class="iter-meta">
                    <span>Cumulative cost: <strong>${it.get('cost_usd', 0):.4f}</strong></span>
                    <span>Tokens: <strong>{it.get('tokens', 0):,}</strong></span>
                </div>
                {stdout_block}
                {ops_block}
            </div>"""

        goal_text = html_lib.escape(config.get("goal", ""))
        run_id = html_lib.escape(config.get("run_id", ""))
        model = html_lib.escape(config.get("model", ""))
        bench = html_lib.escape(config.get("bench_command", ""))
        baseline_display = f"{baseline}" if baseline is not None else "N/A"
        best_display = _fmt_score(best_score) if best_score is not None else "N/A"
        target_display = f"{target}" if target is not None else "—"

        html_out = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>Hone Report — {run_id}</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: #0f172a;
    color: #e2e8f0;
    min-height: 100vh;
    padding: 32px 16px;
  }}
  a {{ color: #60a5fa; }}
  .container {{ max-width: 900px; margin: 0 auto; }}

  /* header */
  .header {{ margin-bottom: 32px; }}
  .header h1 {{ font-size: 1.75rem; font-weight: 700; color: #f1f5f9; letter-spacing: -0.02em; }}
  .header .run-meta {{ margin-top: 6px; font-size: 0.8rem; color: #64748b; display: flex; gap: 16px; flex-wrap: wrap; }}
  .goal-box {{
    margin-top: 14px;
    background: #1e293b;
    border: 1px solid #334155;
    border-left: 3px solid #6366f1;
    border-radius: 8px;
    padding: 14px 16px;
    font-size: 0.9rem;
    color: #cbd5e1;
    line-height: 1.6;
  }}

  /* stat cards */
  .stats {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
    gap: 12px;
    margin-bottom: 32px;
  }}
  .stat-card {{
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 16px;
  }}
  .stat-card .label {{ font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.08em; color: #64748b; margin-bottom: 6px; }}
  .stat-card .value {{ font-size: 1.35rem; font-weight: 700; color: #f1f5f9; }}
  .stat-card .value.green {{ color: #22c55e; }}
  .stat-card .value.blue  {{ color: #60a5fa; }}
  .stat-card .value.amber {{ color: #f59e0b; }}

  /* chart */
  .chart-section {{
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 20px;
    margin-bottom: 32px;
  }}
  .chart-section h2 {{ font-size: 0.9rem; font-weight: 600; color: #94a3b8; margin-bottom: 16px; text-transform: uppercase; letter-spacing: 0.06em; }}
  .chart-wrap {{ position: relative; height: 240px; }}

  /* iterations */
  .section-title {{ font-size: 0.9rem; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 14px; }}
  .iter-card {{
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 18px 20px;
    margin-bottom: 12px;
    border-left-width: 3px;
  }}
  .card-accepted {{ border-left-color: #22c55e; }}
  .card-reverted {{ border-left-color: #ef4444; }}
  .card-error    {{ border-left-color: #fb923c; }}

  .iter-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; flex-wrap: wrap; gap: 8px; }}
  .iter-title {{ display: flex; align-items: center; gap: 10px; }}
  .iter-num {{ font-weight: 600; color: #f1f5f9; }}
  .iter-score {{ font-size: 0.85rem; color: #94a3b8; }}
  .iter-score strong {{ color: #e2e8f0; }}

  .badge {{ display: inline-block; font-size: 0.68rem; font-weight: 600; padding: 2px 8px; border-radius: 99px; text-transform: uppercase; letter-spacing: 0.06em; }}
  .badge-accepted {{ background: #14532d; color: #22c55e; }}
  .badge-reverted {{ background: #450a0a; color: #ef4444; }}
  .badge-error    {{ background: #431407; color: #fb923c; }}

  .hypothesis-block {{ margin-bottom: 12px; }}
  .hypothesis-label {{ display: inline-block; font-size: 0.65rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: #6366f1; background: rgba(99,102,241,0.1); padding: 2px 7px; border-radius: 4px; margin-bottom: 6px; }}
  .reasoning {{ font-size: 0.85rem; color: #94a3b8; line-height: 1.65; }}
  .iter-meta {{ display: flex; gap: 20px; font-size: 0.75rem; color: #64748b; margin-bottom: 10px; }}
  .iter-meta strong {{ color: #94a3b8; }}

  .violations {{ background: #2d1515; border: 1px solid #7f1d1d; border-radius: 6px; padding: 10px 14px; margin-bottom: 10px; font-size: 0.8rem; color: #fca5a5; }}
  .violations ul {{ padding-left: 16px; margin-top: 4px; }}

  details {{ margin-top: 8px; }}
  summary {{
    cursor: pointer;
    font-size: 0.78rem;
    color: #64748b;
    user-select: none;
    padding: 4px 0;
  }}
  summary:hover {{ color: #94a3b8; }}

  .op-block {{ margin-top: 10px; }}
  .op-header {{ font-size: 0.75rem; color: #64748b; margin-bottom: 4px; }}
  .op-type {{ display: inline-block; background: #1d4ed8; color: #bfdbfe; font-size: 0.65rem; font-weight: 700; padding: 1px 6px; border-radius: 4px; text-transform: uppercase; margin-right: 4px; }}

  pre.code-block, pre.stdout-block {{
    background: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 6px;
    padding: 12px 14px;
    font-size: 0.75rem;
    line-height: 1.6;
    overflow-x: auto;
    white-space: pre;
    color: #94a3b8;
    margin-top: 4px;
  }}
  pre.stdout-block {{ color: #6ee7b7; }}
  pre.stdout-error {{ color: #fb923c; }}
  .score-error {{ color: #fb923c; }}
</style>
</head>
<body>
<div class="container">

  <div class="header">
    <h1>Hone Run Report</h1>
    <div class="run-meta">
      <span>Run: <strong>{run_id}</strong></span>
      <span>Model: <strong>{model}</strong></span>
      <span>Bench: <code>{bench}</code></span>
      <span>Direction: <strong>{optimize}</strong></span>
    </div>
    <div class="goal-box">{goal_text}</div>
  </div>

  <div class="stats">
    <div class="stat-card">
      <div class="label">Baseline</div>
      <div class="value">{baseline_display}</div>
    </div>
    <div class="stat-card">
      <div class="label">Best Score</div>
      <div class="value green">{best_display}</div>
    </div>
    <div class="stat-card">
      <div class="label">Improvement</div>
      <div class="value blue">{improvement_label}</div>
    </div>
    <div class="stat-card">
      <div class="label">Target</div>
      <div class="value amber">{target_display}</div>
    </div>
    <div class="stat-card">
      <div class="label">Total Cost</div>
      <div class="value">${final_cost:.4f}</div>
    </div>
    <div class="stat-card">
      <div class="label">Total Tokens</div>
      <div class="value">{final_tokens:,}</div>
    </div>
    <div class="stat-card">
      <div class="label">Iterations</div>
      <div class="value">{len(iterations)}</div>
    </div>
  </div>

  <div class="chart-section">
    <h2>Score over iterations</h2>
    <div class="chart-wrap">
      <canvas id="scoreChart"></canvas>
    </div>
  </div>

  <div class="section-title">Iterations</div>
  {cards_html}

</div>
<script>
(function() {{
  const ctx = document.getElementById('scoreChart');
  const labels = {chart_labels_js};
  const scores = {chart_scores_js};
  const colors = {chart_colors_js};

  new Chart(ctx, {{
    type: 'line',
    data: {{
      labels,
      datasets: [
        {{
          label: 'Score',
          data: scores,
          borderColor: '#6366f1',
          backgroundColor: 'rgba(99,102,241,0.08)',
          pointBackgroundColor: colors,
          pointBorderColor: colors,
          pointRadius: 5,
          pointHoverRadius: 7,
          tension: 0.3,
          fill: true,
          borderWidth: 2,
          spanGaps: false,
        }}
        {baseline_line}
        {target_line}
      ]
    }},
    options: {{
      responsive: true,
      maintainAspectRatio: false,
      interaction: {{ mode: 'index', intersect: false }},
      plugins: {{
        legend: {{
          labels: {{ color: '#64748b', font: {{ size: 11 }} }}
        }},
        tooltip: {{
          backgroundColor: '#1e293b',
          borderColor: '#334155',
          borderWidth: 1,
          titleColor: '#f1f5f9',
          bodyColor: '#94a3b8',
        }}
      }},
      scales: {{
        x: {{
          ticks: {{ color: '#64748b' }},
          grid:  {{ color: '#1e293b' }},
          title: {{ display: true, text: 'Iteration', color: '#475569' }}
        }},
        y: {{
          ticks: {{ color: '#64748b' }},
          grid:  {{ color: '#1e293b' }},
          title: {{ display: true, text: 'Score', color: '#475569' }}
        }}
      }}
    }}
  }});
}})();
</script>
</body>
</html>"""

        self.html_path.write_text(html_out)
