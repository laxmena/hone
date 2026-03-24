import shutil
import subprocess
from pathlib import Path
from uuid import uuid4
from . import Config, HoneSnapshotError

class SnapshotStrategy:
    def take(self) -> str: raise NotImplementedError
    def revert(self, snap_id: str): raise NotImplementedError

class CopySnapshot(SnapshotStrategy):
    def __init__(self, config: Config):
        self.workspace = config.workspace
        self.snap_dir = self.workspace / ".hone" / "runs" / config.run_id / "snapshots"
        self.files = config.files
    
    def _scoped_files(self):
        out = []
        for f in self.files:
            p = (self.workspace / f).resolve()
            if p.is_file(): out.append(p)
            elif p.is_dir(): out.extend([c for c in p.rglob("*") if c.is_file() and '.git' not in c.parts])
        return out

    def take(self) -> str:
        from datetime import datetime
        snap_id = f"{datetime.now().strftime('%H%M%S')}_{uuid4().hex[:4]}"
        dest_dir = self.snap_dir / snap_id
        for path in self._scoped_files():
            dest = dest_dir / path.relative_to(self.workspace)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dest)
        return snap_id

    def revert(self, snap_id: str):
        src_dir = self.snap_dir / snap_id
        for src in src_dir.rglob("*"):
            if src.is_file():
                dest = self.workspace / src.relative_to(src_dir)
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dest)

class GitSnapshot(SnapshotStrategy):
    def __init__(self, config: Config):
        self.workspace = config.workspace

    def take(self) -> str:
        snap_id = f"hone-{uuid4().hex[:8]}"
        try:
            subprocess.run(
                ["git", "stash", "push", "-m", snap_id, "--include-untracked"],
                cwd=self.workspace, check=True, capture_output=True, text=True
            )
        except subprocess.CalledProcessError as e:
            raise HoneSnapshotError(f"Git stash failed: {e.stderr}")
        return snap_id

    def revert(self, snap_id: str):
        result = subprocess.run(
            ["git", "stash", "list"], cwd=self.workspace,
            capture_output=True, text=True
        )
        for line in result.stdout.splitlines():
            if snap_id in line:
                idx = line.split(":")[0]
                subprocess.run(
                    ["git", "stash", "apply", idx],
                    cwd=self.workspace, check=True
                )
                return
        raise HoneSnapshotError(f"Snapshot {snap_id} not found in git stash")

class Snapshot:
    def __init__(self, config: Config):
        if config.snapshot_strategy == "git":
            self.strategy = GitSnapshot(config)
        else:
            self.strategy = CopySnapshot(config)
            
    def take(self) -> str: return self.strategy.take()
    def revert(self, snap_id: str): self.strategy.revert(snap_id)
