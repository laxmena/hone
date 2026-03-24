import pytest
from pathlib import Path
from hone import Config, HoneSandboxError, RunOperation, WriteOperation, Operations
from hone.sandbox import Sandbox

def test_safe_path(tmp_path):
    cfg = Config("g", "b", None, [], [], "h", 1, "m", None, 60, False, None, "copy", "x", tmp_path)
    sb = Sandbox(cfg)
    
    assert sb._safe_path("foo.txt") == (tmp_path / "foo.txt").resolve()
    
    with pytest.raises(HoneSandboxError):
        sb._safe_path("../escaped.txt")

def test_run_allowlist(tmp_path):
    cfg = Config("g", "b", None, [], [], "h", 1, "m", None, 60, False, None, "copy", "x", tmp_path)
    sb = Sandbox(cfg)
    
    with pytest.raises(HoneSandboxError, match="not in allowlist"):
        sb._run(RunOperation(command="rm -rf /"))
