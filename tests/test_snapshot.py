import pytest
from pathlib import Path
from hone import Config
from hone.snapshot import Snapshot

def test_copy_snapshot(tmp_path):
    (tmp_path / "a.txt").write_text("v1")
    cfg = Config("g", "b", None, [], ["a.txt"], "h", 1, "m", None, 60, False, None, "copy", "run1", tmp_path)
    snap = Snapshot(cfg)
    
    sid = snap.take()
    assert (tmp_path / "a.txt").exists()
    
    (tmp_path / "a.txt").write_text("v2")
    snap.revert(sid)
    assert (tmp_path / "a.txt").read_text() == "v1"
