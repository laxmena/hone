import subprocess
import re
from typing import List
from . import Config, BenchmarkResult, HoneBenchmarkError

class Benchmark:
    def __init__(self, config: Config):
        self.config = config

    def run(self) -> BenchmarkResult:
        try:
            result = subprocess.run(
                self.config.bench_command,
                shell=True,
                cwd=self.config.workspace,
                capture_output=True,
                text=True,
                timeout=self.config.timeout
            )
        except subprocess.TimeoutExpired:
            raise HoneBenchmarkError(f"Benchmark timed out after {self.config.timeout}s")

        stdout = result.stdout
        stderr = result.stderr

        score = self._extract_score(stdout)
        violations = self._check_constraints(stdout)

        return BenchmarkResult(
            score=score,
            stdout=stdout,
            stderr=stderr,
            constraint_violations=violations,
            constraints=self.config.constraints,
        )

    def _extract_score(self, stdout: str) -> float:
        if self.config.score_pattern:
            match = re.search(self.config.score_pattern, stdout)
            if match:
                try: return float(match.group(1))
                except (ValueError, IndexError): pass
        
        matches = re.findall(r"[-+]?\d*\.\d+|\d+", stdout)
        if matches:
            return float(matches[-1])
        raise HoneBenchmarkError("Could not extract score from benchmark output.")

    def _check_constraints(self, stdout: str) -> List[str]:
        # Basic constraint functionality to be expanded
        return []
