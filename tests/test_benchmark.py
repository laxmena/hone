import pytest
from pathlib import Path
from hone import Config, BenchmarkResult, HoneBenchmarkError
from hone.benchmark import Benchmark

def test_extract_score_default():
    cfg = Config("goal", "echo 10.5", None, [], [], "higher", 1, "m", None, 60, False, None, "copy", "x", Path.cwd())
    b = Benchmark(cfg)
    assert b._extract_score("some output 42.0 done") == 42.0
    assert b._extract_score("100") == 100.0

def test_extract_score_pattern():
    cfg = Config("goal", "x", None, [], [], "higher", 1, "m", r"Score: (\d+\.\d+)", 60, False, None, "copy", "x", Path.cwd())
    b = Benchmark(cfg)
    assert b._extract_score("Stats\nScore: 99.9\nDone") == 99.9
