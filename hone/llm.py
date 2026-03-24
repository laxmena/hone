import json
import re
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple

from . import Config, LoopState, Operations, HoneLLMError, HoneParseError, BenchmarkResult

SYSTEM_PROMPT = """
You are an autonomous optimization agent. Your job is to improve software against a benchmark.

Respond ONLY with valid JSON:
{
  "reasoning": "one line — your brief hypothesis and what you will change",
  "operations": [
    {"type": "write",  "path": "relative/path", "content": "full file content"},
    {"type": "patch",  "path": "relative/path", "diff": "unified diff string"},
    {"type": "delete", "path": "relative/path"},
    {"type": "run",    "command": "shell command"}
  ]
}

Rules:
- Stay within scoped files/directories.
- Prefer "patch" over "write" for files > 50 lines.
- One focused hypothesis per iteration.
- Simplicity criterion: All else being equal, simpler is better. Weigh complexity cost against improvement magnitude. A marginal gain for ugly code is not worth it. Deleting code while maintaining performance is a great outcome.
- Crashes: If a run crashes with a simple error (e.g. syntax, typo), use your reasoning to fix it on the next run. If the idea is fundamentally broken, try a completely different approach.
- If last iteration was reverted, do NOT repeat the same mistake.
"""

COST_PER_1K_TOKENS = {
    "claude-haiku-4-5":           {"input": 0.003,  "output": 0.015},
    "claude-sonnet-4-6":          {"input": 0.003,  "output": 0.015},
    "gpt-4o":                     {"input": 0.005,  "output": 0.015},
    "gpt-4o-mini":                {"input": 0.00015,"output": 0.0006},
}

def compute_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    rates = COST_PER_1K_TOKENS.get(model, {"input": 0.0, "output": 0.0})
    return (input_tokens * rates["input"] + output_tokens * rates["output"]) / 1000

@dataclass
class LLMUsage:
    input_tokens:  int
    output_tokens: int
    total_tokens:  int
    cost_usd:      float

def extract_json(response: str) -> str:
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", response, re.DOTALL)
    if match: return match.group(1)
    match = re.search(r"(\{.*\})", response, re.DOTALL)
    if match: return match.group(1)
    return response

def read_scoped_files(config: Config) -> str:
    out = []
    for f in config.files:
        p = (config.workspace / f).resolve()
        if p.is_file():
            try: out.append(f"--- {f} ---\n{p.read_text(errors='ignore')}")
            except: pass
        elif p.is_dir():
            for child in p.rglob("*"):
                if child.is_file() and not '.git' in child.parts:
                    try: out.append(f"--- {child.relative_to(config.workspace)} ---\n{child.read_text(errors='ignore')}")
                    except: pass
    return "\n\n".join(out)

class ClientWrapper:
    def complete(self, system: str, messages: List[Dict[str, str]], model: str) -> Tuple[str, LLMUsage]:
        raise NotImplementedError

class OpenAIClient(ClientWrapper):
    def complete(self, system: str, messages: List[Dict[str, str]], model: str) -> Tuple[str, LLMUsage]:
        import openai
        client = openai.OpenAI()
        sys_msg = [{"role": "system", "content": system}]
        response = client.chat.completions.create(
            model=model,
            messages=sys_msg + messages,
        )
        msg = response.choices[0].message.content
        usage = response.usage
        cost = compute_cost(model, usage.prompt_tokens, usage.completion_tokens)
        return msg, LLMUsage(usage.prompt_tokens, usage.completion_tokens, usage.total_tokens, cost)

class AnthropicClient(ClientWrapper):
    def complete(self, system: str, messages: List[Dict[str, str]], model: str) -> Tuple[str, LLMUsage]:
        import anthropic
        client = anthropic.Anthropic()
        response = client.messages.create(
            model=model,
            system=system,
            messages=messages,
            max_tokens=4096,
        )
        msg = response.content[0].text
        usage = response.usage
        cost = compute_cost(model, usage.input_tokens, usage.output_tokens)
        return msg, LLMUsage(usage.input_tokens, usage.output_tokens, usage.input_tokens + usage.output_tokens, cost)

class OllamaClient(ClientWrapper):
    def complete(self, system: str, messages: List[Dict[str, str]], model: str) -> Tuple[str, LLMUsage]:
        import ollama
        sys_msg = [{"role": "system", "content": system}]
        response = ollama.chat(model=model, messages=sys_msg + messages)
        msg = response['message']['content']
        # mock usage for local models (free)
        return msg, LLMUsage(0, 0, 0, 0.0)

def build_client(config: Config) -> ClientWrapper:
    if "claude" in config.model: return AnthropicClient()
    if "gpt" in config.model: return OpenAIClient()
    return OllamaClient()

class LLM:
    def __init__(self, config: Config):
        self.config       = config
        self.conversation = []
        self.client       = build_client(config)

    def ask(self, state: LoopState) -> Tuple[Operations, LLMUsage]:
        if not self.conversation:
            self.conversation.append({
                "role": "user",
                "content": self._initial_prompt(state)
            })

        response, usage = self._call()
        self.conversation.append({"role": "assistant", "content": response})
        ops = self._parse(response)
        return ops, usage

    def report_back(self, result: BenchmarkResult, accepted: bool):
        status = "accepted ✓" if accepted else "reverted ✗"
        msg = (
            f"Result: {result.score} — {status}\n\n"
            f"Benchmark output:\n{result.stdout}"
        )
        if result.constraint_violations:
            msg += f"\n\nConstraint violations: {result.constraint_violations}"
        msg += "\n\nContinue."
        self.conversation.append({"role": "user", "content": msg})

    def _call(self) -> Tuple[str, LLMUsage]:
        for attempt in range(2):
            try:
                return self.client.complete(
                    system=SYSTEM_PROMPT,
                    messages=self.conversation,
                    model=self.config.model,
                )
            except Exception as e:
                if attempt == 1:
                    raise HoneLLMError(str(e))

    def _parse(self, response: str) -> Operations:
        try:
            data = json.loads(extract_json(response))
            return Operations.from_dict(data)
        except (json.JSONDecodeError, KeyError) as e:
            raise HoneParseError(f"Bad LLM response: {e}")

    def _initial_prompt(self, state: LoopState) -> str:
        return (
            f"Goal: {self.config.goal}\n"
            f"Optimize: {self.config.optimize}\n"
            f"Target: {self.config.target or 'maximize'}\n"
            f"Constraints: {self.config.constraints or 'none'}\n"
            f"Baseline: {state.baseline}\n\n"
            f"Files:\n{read_scoped_files(self.config)}\n\n"
            f"Begin."
        )
