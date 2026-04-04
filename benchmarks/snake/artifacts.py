import json
import os
from datetime import datetime
from typing import Dict, Any

class ArtifactWriter:
    """
    Writes decision-level logs (JSONL) and episode summaries (JSON).
    Designed for reproducibility and Zenodo archiving.
    """
    def __init__(self, root="artifacts/snake"):
        self.root = root
        os.makedirs(self.root, exist_ok=True)
        self.session_id = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        self.decisions_path = os.path.join(self.root, f"decisions_{self.session_id}.jsonl")
        self.summary_path = os.path.join(self.root, f"summary_{self.session_id}.json")

    def write_decision(self, record: Dict[str, Any]):
        with open(self.decisions_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

    def write_summary(self, summary: Dict[str, Any]):
        with open(self.summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
