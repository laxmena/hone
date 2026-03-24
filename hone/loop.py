import signal
import sys
from . import Config, LoopState, BenchmarkResult, Operations
from .snapshot import Snapshot
from .benchmark import Benchmark
from .llm import LLM
from .log import Log
from .report import Report
from .sandbox import Sandbox

def print_baseline(baseline: BenchmarkResult, dry_run: bool):
    print(f"\n  baseline    {baseline.score}")
    if dry_run:
        print("\n  dry-run — no changes will be applied\n")

def print_budget_stop(cost: float, budget: float):
    print(f"\n  stopped — budget exceeded (${cost:.2f} >= ${budget:.2f})")

def print_dry_run(ops: Operations):
    print("  iter  1  (planned)")
    print(f"    reasoning: {ops.reasoning}")
    print("    operations:")
    for op in ops.operations:
        print(f"      {op.type}   {getattr(op, 'path', getattr(op, 'command', ''))}")
    print("\n  stopped — dry-run complete")

def print_iteration(n: int, result: BenchmarkResult, accepted: bool, reasoning: str, state: LoopState):
    arrow = "↑" if accepted else "↓"
    cost_str = f"${state.cost_usd:.2f}"
    reasoning_short = reasoning.split('\n')[0][:50] + ("..." if len(reasoning.split('\n')[0]) > 50 else "")
    score_str = f"{result.score:<5.2f}" if isinstance(result.score, float) else str(result.score)
    print(f"  iter {n:2d}  {arrow}  {score_str:<5}   {reasoning_short:<45} {cost_str}")
    
    if result.score in (float('inf'), float('-inf')):
        err = result.stderr.strip() if result.stderr else (result.constraint_violations[0] if result.constraint_violations else "")
        if err:
            err_line = err.split('\n')[-1]
            if len(err_line) > 80: err_line = err_line[:77] + "..."
            from rich.console import Console
            Console().print(f"           [dim red]↳ {err_line}[/dim red]")

def print_summary(state: LoopState, log: Log):
    print(f"\n  done    {state.baseline} → {state.best_score}   {state.iteration} iterations   ${state.cost_usd:.2f}\n")
    
    if not log.data.get("iterations"): return
    
    print("  --- EXPERIMENT LOG ---")
    print(f"  {'Iter':<4} | {'Status':<8} | {'Score':<8} | {'Description'}")
    print("  " + "-"*75)
    for it in log.data["iterations"]:
        score_val = it["score"]
        status = "keep" if it["accepted"] else ("crash" if score_val in (float('inf'), float('-inf')) else "discard")
        desc = it["reasoning"].replace('\n', ' ')
        if len(desc) > 60: desc = desc[:57] + "..."
        score_str = f"{score_val:.4f}" if isinstance(score_val, float) else str(score_val)
        print(f"  {it['n']:<4} | {status:<8} | {score_str:<8} | {desc}")
    print()

class Loop:
    def __init__(self, config: Config):
        self.config   = config
        self.snapshot = Snapshot(config)
        self.bench    = Benchmark(config)
        self.llm      = LLM(config)
        self.log      = Log(config)
        self.sandbox  = Sandbox(config)
        self.state    = None

    def start(self):
        signal.signal(signal.SIGINT, self._handle_interrupt)

        initial_snap = self.snapshot.take()
        baseline     = self.bench.run()
        self.state   = LoopState(
            baseline      = baseline.score,
            best_score    = baseline.score,
            best_snapshot = initial_snap,
        )

        self.log.write_baseline(baseline)
        print_baseline(baseline, dry_run=self.config.dry_run)

        for i in range(1, self.config.max_iterations + 1):
            if self.state.stopped:
                break
            self.state.iteration = i
            done = self._iterate(i)
            if done:
                break

        self._finalize()

    def _iterate(self, n: int) -> bool:
        try:
            # ask
            ops, usage = self.llm.ask(self.state)

            # track cost — hard stop if budget exceeded
            self.state.tokens_used += usage.total_tokens
            self.state.cost_usd    += usage.cost_usd
            if self.config.budget_usd and self.state.cost_usd >= self.config.budget_usd:
                print_budget_stop(self.state.cost_usd, self.config.budget_usd)
                self.state.stopped = True
                return False

            # dry-run: print and exit after first iteration
            if self.config.dry_run:
                print_dry_run(ops)
                return True   # stops loop

            # act (sandboxed) and measure
            self.sandbox.apply(ops)
            result = self.bench.run()
        except Exception as e:
            worst_score = float('inf') if self.config.optimize == "lower" else float('-inf')
            result = BenchmarkResult(
                score=worst_score,
                stdout="",
                stderr=str(e),
                constraint_violations=[f"Iteration Error: {e}"],
                constraints=self.config.constraints
            )
            if 'ops' not in locals():
                ops = Operations(reasoning=f"Crash parsed: {e}", operations=[])

        # decide
        accepted = self._is_improvement(result)
        if accepted:
            snap = self.snapshot.take()
            self.state.best_score    = result.score
            self.state.best_snapshot = snap
        else:
            self.snapshot.revert(self.state.best_snapshot)

        # persist + print
        self.log.write_iteration(n, ops, result, accepted, self.state)
        print_iteration(n, result, accepted, ops.reasoning, self.state)

        # continue conversation
        self.llm.report_back(result, accepted)

        target_reached = self._target_reached(result.score)
        if target_reached:
            print("  ✓ target reached")
        elif not self.state.stopped:
            import time
            time.sleep(3.5)  # Pause to prevent API rate limiting on deep loops
            
        return target_reached

    def _is_improvement(self, result: BenchmarkResult) -> bool:
        if result.constraint_violations:
            return False
        if self.config.optimize == "higher":
            return result.score > self.state.best_score
        return result.score < self.state.best_score

    def _target_reached(self, score: float) -> bool:
        if self.config.target is None:
            return False
        if self.config.optimize == "higher":
            return score >= self.config.target
        return score <= self.config.target

    def _handle_interrupt(self, sig, frame):
        print("\n  stopping after this iteration...")
        if self.state:
            self.state.stopped = True
        else:
            sys.exit(1)

    def _finalize(self):
        self.log.close(self.state)
        Report(self.config).generate()
        print_summary(self.state, self.log)
