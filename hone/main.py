import click
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

from . import Config
from .loop import Loop

def timestamp_id() -> str:
    return datetime.now().strftime("%Y-%m-%d_%H%M%S")

def default_model() -> str:
    return "claude-haiku-4-5"

@click.command()
@click.argument("goal", default="")
@click.option("--goal-file",           type=click.Path(exists=True, dir_okay=False),
              help="Path to a file containing the goal (alternative to the GOAL argument)")
@click.option("--bench",               required=True)
@click.option("--target",              type=float)
@click.option("--constraint",          multiple=True)
@click.option("--files",               multiple=True)
@click.option("--optimize",            default="higher",
                                       type=click.Choice(["higher", "lower"]))
@click.option("--max-iter",            default=20,    type=int)
@click.option("--model",               default=None)
@click.option("--score-pattern",       default=None)
@click.option("--timeout",             default=60,    type=int)
@click.option("--dry-run",             is_flag=True,
              help="Show planned operations without applying them")
@click.option("--budget",              default=None,  type=float,
              help="Hard stop at this USD cost (e.g. 1.00)")
@click.option("--snapshot-strategy",   default="copy",
                                       type=click.Choice(["copy", "git"]))
def run(goal, goal_file, bench, target, constraint, files, optimize, max_iter,
        model, score_pattern, timeout, dry_run, budget, snapshot_strategy):
    if goal_file:
        goal = Path(goal_file).read_text()
    if not goal:
        raise click.UsageError("Provide either the GOAL argument or --goal-file.")
    config = Config(
        goal=goal,
        bench_command=bench,
        target=target,
        constraints=list(constraint),
        files=list(files) or ["."],
        optimize=optimize,
        max_iterations=max_iter,
        model=model or default_model(),
        score_pattern=score_pattern,
        timeout=timeout,
        dry_run=dry_run,
        budget_usd=budget,
        snapshot_strategy=snapshot_strategy,
        run_id=timestamp_id(),
        workspace=Path.cwd(),
    )
    Loop(config).start()

if __name__ == "__main__":
    run()
