import pytest
from pathlib import Path
from hone import Config, LoopState
from hone.loop import Loop

def test_loop_init(tmp_path):
    cfg = Config("g", "b", None, [], [], "h", 1, "m", None, 60, False, None, "copy", "x", tmp_path)
    loop = Loop(cfg)
    assert loop.config == cfg
    assert loop.state is None
