import json
from pathlib import Path
from . import Config, LoopState

class Log:
    def __init__(self, config: Config):
        self.dir = config.workspace / ".hone" / "runs" / config.run_id
        self.dir.mkdir(parents=True, exist_ok=True)
        self.path = self.dir / "run.json"
        
        cfg_dict = config.__dict__.copy()
        if 'workspace' in cfg_dict:
            cfg_dict['workspace'] = str(cfg_dict['workspace'])

        self.data = {
            "config": cfg_dict,
            "iterations": [],
            "baseline": None,
            "best_score": None,
            "final_cost": 0.0,
            "final_tokens": 0
        }

    def _flush(self):
        self.path.write_text(json.dumps(self.data, indent=2))

    def write_baseline(self, result):
        self.data["baseline"] = {
            "score": result.score,
            "stdout": result.stdout
        }
        self.data["best_score"] = result.score
        self._flush()

    def write_iteration(self, n, ops, result, accepted, state: LoopState):
        self.data["iterations"].append({
            "n": n,
            "score": result.score,
            "accepted": accepted,
            "reasoning": ops.reasoning,
            "operations": ops.to_dict()["operations"],
            "constraints": result.constraints,
            "violations": result.constraint_violations,
            "stdout": result.stdout,
            "cost_usd": state.cost_usd,
            "tokens": state.tokens_used,
        })
        self.data["best_score"] = state.best_score
        self._flush()

    def close(self, state: LoopState):
        self.data["final_cost"] = state.cost_usd
        self.data["final_tokens"] = state.tokens_used
        self._flush()
