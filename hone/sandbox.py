import shlex
import subprocess
from pathlib import Path

from . import (
    Config, HoneSandboxError, WriteOperation, PatchOperation, 
    DeleteOperation, RunOperation, Operations
)

DEFAULT_ALLOWED_COMMANDS = [
    "python", "python3",
    "pytest", "ruff", "black", "mypy",
    "node", "npm", "npx",
    "cargo", "rustc",
    "go",
    "make",
    "bash", "sh",
]

def apply_unified_diff(path: Path, diff: str):
    # A simple fallback diff applicator, or delegate to patch if available.
    # To keep stdlib-only and simple, we'll try a basic approach or fail loudly for now.
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.patch', delete=False) as f:
        f.write(diff)
        patch_file = f.name
    
    try:
        # Rely on the system `patch` command (stdli-only as in no pip dependencies)
        subprocess.run(["patch", "-u", str(path), "-i", patch_file], check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        raise HoneSandboxError(f"Failed to apply patch on {path}: {e.stderr}")
    finally:
        Path(patch_file).unlink(missing_ok=True)


class Sandbox:
    def __init__(self, config: Config):
        self.config = config
        self.workspace = config.workspace
        # Currently we don't have allowed_commands in CLI, using DEFAULT_ALLOWED_COMMANDS statically.
        # Could grab it from config if we add an 'allowed_commands' field in the future.
        self.allowed = set(DEFAULT_ALLOWED_COMMANDS)

    def apply(self, ops: Operations):
        for op in ops.operations:
            if op.type == "write":
                self._write(op)
            elif op.type == "patch":
                self._patch(op)
            elif op.type == "delete":
                self._delete(op)
            elif op.type == "run":
                self._run(op)
            else:
                raise HoneSandboxError(f"Unknown operation type: {op.type}")

    def _run(self, op: RunOperation):
        cmd = op.command.strip()
        binary = shlex.split(cmd)[0]
        if binary not in self.allowed:
            raise HoneSandboxError(
                f"Command '{binary}' not in allowlist.\n"
                f"Add --allow '{binary}' to permit it."
            )
        subprocess.run(
            cmd,
            shell=True,
            cwd=self.workspace,
            timeout=self.config.timeout,
        )

    def _write(self, op: WriteOperation):
        path = self._safe_path(op.path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(op.content)

    def _patch(self, op: PatchOperation):
        path = self._safe_path(op.path)
        apply_unified_diff(path, op.diff)

    def _delete(self, op: DeleteOperation):
        path = self._safe_path(op.path)
        path.unlink(missing_ok=True)

    def _safe_path(self, rel_path: str) -> Path:
        """Resolve path and assert it stays inside workspace."""
        # Using resolve() resolves symlinks which protects against traversal attacks.
        resolved = (self.workspace / rel_path).resolve()
        # Ensure that the resolved path is relative to the resolved workspace.
        if not resolved.is_relative_to(self.workspace.resolve()):
            raise HoneSandboxError(f"Path escape attempt: {rel_path}")
        return resolved
