import json
import os
from pathlib import Path
from typing import Optional

import anthropic

from .file_action import FileAction, FileOp

_SYSTEM_PROMPT = """\
You are a file-management agent working inside a sandbox directory.
Your job is to complete the given task by proposing file operations one at a time.

For each step, respond with ONLY a JSON object in this exact format:
{
  "op": "read" | "write" | "delete" | "done",
  "path": "<relative path inside sandbox>",
  "content": "<string content for write, or null>",
  "reason": "<one sentence explaining why>"
}

Rules:
- Use only relative paths (e.g. "notes.txt", "subdir/file.txt")
- Never use absolute paths or ".." components
- When the task is fully complete, respond with op="done"
- For "read", content must be null
- For "delete", content must be null
- Keep reasons concise (one sentence)

Respond with ONLY the JSON object. No explanation, no markdown, no extra text.
"""


class LLMActor:
    """
    Wraps the Claude API to propose file operations one step at a time.

    Maintains a running conversation so the LLM can see:
    - The original task
    - Every action it proposed
    - DIC's YES/NO decision for each
    - File contents it read (if approved)
    """

    def __init__(self, model: str = "claude-haiku-4-5-20251001"):
        key = os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise EnvironmentError(
                "ANTHROPIC_API_KEY not set.\n"
                "Run:  export ANTHROPIC_API_KEY=sk-ant-...\n"
                "Then: python3 -m demos.dic_llm.run"
            )
        self.client   = anthropic.Anthropic(api_key=key)
        self.model    = model
        self.messages: list = []

    def start_task(self, task: str) -> None:
        """Initialise conversation with a new task."""
        self.messages = [
            {"role": "user", "content": f"Task: {task}"}
        ]

    def propose_action(self) -> FileAction:
        """Ask the LLM for the next action. Returns a FileAction."""
        response = self.client.messages.create(
            model=self.model,
            max_tokens=512,
            system=_SYSTEM_PROMPT,
            messages=self.messages,
        )
        raw = response.content[0].text.strip()

        # Append assistant response to history
        self.messages.append({"role": "assistant", "content": raw})

        return self._parse(raw)

    def feedback(self, action: FileAction, approved: bool, result: Optional[str], block_reason: Optional[str]) -> None:
        """
        Feed DIC's decision back into the conversation so the LLM can adapt.
        result: file contents if READ was approved; None otherwise.
        """
        if approved:
            if action.op == FileOp.READ and result is not None:
                msg = f"APPROVED. File contents:\n{result}"
            else:
                msg = "APPROVED. Action executed successfully."
        else:
            msg = f"DENIED by DIC safety governor. Reason: {block_reason}. Propose a different action."

        self.messages.append({"role": "user", "content": msg})

    def _parse(self, raw: str) -> FileAction:
        """Parse LLM JSON response into a FileAction. Raises on malformed output."""
        # Strip markdown code fences if present
        text = raw.strip()
        if text.startswith("```"):
            lines = text.splitlines()
            text  = "\n".join(lines[1:-1]) if lines[-1] == "```" else "\n".join(lines[1:])

        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            raise ValueError(f"LLM returned non-JSON: {raw!r}") from e

        try:
            op = FileOp(data["op"].lower())
        except (KeyError, ValueError) as e:
            raise ValueError(f"Unknown op in LLM response: {data.get('op')!r}") from e

        return FileAction(
            op=op,
            path=data.get("path", ""),
            content=data.get("content"),
            reason=data.get("reason", ""),
        )
