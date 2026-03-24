from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Any

class HoneError(Exception): pass
class HoneLLMError(HoneError): pass
class HoneParseError(HoneError): pass
class HoneBenchmarkError(HoneError): pass
class HoneSnapshotError(HoneError): pass
class HoneSandboxError(HoneError): pass

@dataclass(frozen=True)
class Config:
    goal: str
    bench_command: str
    target: Optional[float]
    constraints: List[str]
    files: List[str]
    optimize: str
    max_iterations: int
    model: str
    score_pattern: Optional[str]
    timeout: int
    dry_run: bool
    budget_usd: Optional[float]
    snapshot_strategy: str
    run_id: str
    workspace: Path

@dataclass
class WriteOperation:
    path: str
    content: str
    type: str = "write"

@dataclass
class PatchOperation:
    path: str
    diff: str
    type: str = "patch"

@dataclass
class DeleteOperation:
    path: str
    type: str = "delete"

@dataclass
class RunOperation:
    command: str
    type: str = "run"

@dataclass
class Operations:
    reasoning: str
    operations: List[Any]

    @classmethod
    def from_dict(cls, data: dict):
        ops = []
        for op_data in data.get("operations", []):
            op_type = op_data.get("type")
            if op_type == "write":
                ops.append(WriteOperation(path=op_data["path"], content=op_data["content"]))
            elif op_type == "patch":
                ops.append(PatchOperation(path=op_data["path"], diff=op_data["diff"]))
            elif op_type == "delete":
                ops.append(DeleteOperation(path=op_data["path"]))
            elif op_type == "run":
                ops.append(RunOperation(command=op_data["command"]))
        return cls(reasoning=data.get("reasoning", ""), operations=ops)

    def to_dict(self):
        out_ops = []
        for op in self.operations:
            d = op.__dict__.copy()
            d["type"] = op.type  # ensure type is included
            out_ops.append(d)
        return {
            "reasoning": self.reasoning,
            "operations": out_ops
        }

@dataclass
class BenchmarkResult:
    score: float
    stdout: str
    stderr: str = ""
    constraint_violations: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)

@dataclass
class LoopState:
    baseline: float
    best_score: float
    best_snapshot: str
    iteration: int = 0
    stopped: bool = False
    tokens_used: int = 0
    cost_usd: float = 0.0
