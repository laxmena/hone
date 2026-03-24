import json
from pathlib import Path
from . import Config

class Report:
    def __init__(self, config: Config):
        self.dir = config.workspace / ".hone" / "runs" / config.run_id
        self.json_path = self.dir / "run.json"
        self.html_path = self.dir / "report.html"

    def generate(self):
        if not self.json_path.exists():
            return
        
        data = json.loads(self.json_path.read_text())
        
        html = f"""
        <html>
        <head>
            <title>Hone Report - {data['config']['goal']}</title>
            <style>
                body {{ font-family: sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }}
                .iteration {{ border: 1px solid #ccc; padding: 10px; margin-bottom: 10px; border-radius: 4px; }}
                .accepted {{ border-left: 4px solid green; }}
                .reverted {{ border-left: 4px solid red; }}
                pre {{ background: #f5f5f5; padding: 10px; border-radius: 4px; overflow-x: auto; }}
            </style>
        </head>
        <body>
            <h1>Hone Run Report</h1>
            <p><strong>Goal:</strong> {data['config']['goal']}</p>
            <p><strong>Baseline:</strong> {data.get('baseline', dict()).get('score', 'N/A')}</p>
            <p><strong>Best Score:</strong> {data.get('best_score', 'N/A')}</p>
            <p><strong>Total Cost:</strong> ${data.get('final_cost', 0):.2f}</p>
            <p><strong>Total Tokens:</strong> {data.get('final_tokens', 0)}</p>
            
            <h2>Iterations</h2>
        """
        
        for it in data.get("iterations", []):
            status_class = "accepted" if it["accepted"] else "reverted"
            status_text = "Accepted" if it["accepted"] else "Reverted"
            html += f"""
            <div class="iteration {status_class}">
                <h3>Iteration {it['n']} - Score: {it['score']} ({status_text})</h3>
                <p><strong>Cost Cumulative:</strong> ${it.get('cost_usd', 0):.2f}</p>
                <p><strong>Reasoning:</strong> {it['reasoning']}</p>
                <pre><code>{json.dumps(it['operations'], indent=2)}</code></pre>
            </div>
            """
            
        html += """
        </body>
        </html>
        """
        self.html_path.write_text(html)
