# Hone

Hone automates software optimization. You give it a benchmark command and a target score. Hone rewrites your code until it wins.

It operates entirely autonomously in your terminal. It writes code, runs your benchmark, evaluates the crash or score, and loops. It learns from its own tracebacks. It never stops until it hits your target or exhausts its budget. 

This project is inspired by Karpathy's [autoresearch](https://github.com/karpathy/autoresearch) project.

## How it works

Hone combines minimal orchestration with LLMs. Each experiment runs cleanly. 

- **Statefulness**: It tracks cost, tokens, and git diffs per iteration.
- **Self-Healing**: It catches its own Python tracebacks and feeds them back into the LLM context.
- **Simplicity**: It prioritizes simpler code over complex, marginal gains.
- **Traceability**: It logs an exact chronological timeline of every hypothesis and benchmark score.

## Installation

```bash
git clone https://github.com/laxmena/hone.git
cd hone
python -m venv venv
source venv/bin/activate
pip install -e .
```

You need an `.env` file with your API keys. Hone defaults to `claude-haiku-4-5`.

## Usage

Define your goal and point Hone at your benchmark script.

```bash
hone "Optimize process_logs.py to run under 0.02 seconds. Think creatively." \
  --bench "python bench_logs.py" \
  --files "process_logs.py" \
  --optimize lower \
  --target 0.02 \
  --budget 2.0
```

Hone handles the rest.


## The Log Parser Experiment

I challenged Hone to optimize a naive Python log parser. The baseline script took 1.54 seconds to analyze a 150,000-line server log.

I launched the agent with this exact instruction:

```bash
hone "Optimize process_logs.py to run under 0.02 seconds. Instead of tracking unique IP strings, implement a probabilistic data structure like a fast HyperLogLog to estimate IP uniqueness, or bypass loading string parts entirely." \
  --bench "python examples/log_parser/bench_logs.py" \
  --files "examples/log_parser/process_logs.py" \
  --optimize lower \
  --target 0.02 \
  --score-pattern "Time Taken:\s*(\d+\.\d+)" \
  --budget 2.0
```

Hone launched into a 20-iteration loop. It stripped out slow Python dictionaries. It bypassed memory-heavy `readlines()`. It pre-bound `set.add` to skip language overhead. It hit the physical boundaries of single-threaded Python looping at 0.07 seconds.

When standard file streaming plateaued, Hone changed the rules. It abandoned line-by-line parsing entirely. It read the file into a raw binary blob. It deployed a highly tuned, low-backtracking regular expression to extract targets en masse. 

The final result ran in **0.037 seconds**. Hone achieved a 41x speedup entirely by itself:

```text
  Iter | Status   | Score  | Description
  ...
  18   | keep     | 0.0507 | The real bottleneck is likely the Python loop itself and split() calls. Try using a compiled regex to extract endpoint in one operation...
  19   | keep     | 0.0473 | Great! Regex is faster at 0.0507s. Further optimization: use simpler regex that's more efficient.
  20   | keep     | 0.0370 | Excellent! 0.0473s with simpler regex. Try processing the entire file at once with re.findall() to avoid line iteration overhead...
```

[View the full HTML generated report](.hone/runs/2026-03-23_190242/report.html)

## The Distance Calculation Experiment

Hone optimized real-time taxi dispatch. Finding the nearest driver matters only if it's instantaneous.

Run 1 hit 0.1496s with spatial grid indexing and Manhattan distance pre-filtering. A 14.6x speedup from the 2.18s baseline.

Run 2 achieved 0.069s by changing one thing: stop searching the moment you find a driver. Expand the search radius incrementally instead of checking every driver at once. Another 2.1x speedup.

The AI learned that algorithm beats data structure. Grid resolution barely mattered. Early termination dominated.

[Run 1 report](.hone/runs/2026-03-23_193401/report.html) | [Run 2 report](.hone/runs/2026-03-23_194137/report.html)
