"""
State management for resumable foundation loop.
Tracks layer status, scores, iterations, and propagation debts.
"""

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .provider import content_hash

DEFAULT_STATE = {
    "phase": "foundation",
    "iteration": 0,
    "scores": {
        "world_depth": 0.0,
        "character_depth": 0.0,
        "outline_completeness": 0.0,
        "foreshadowing_balance": 0.0,
        "internal_consistency": 0.0,
    },
    "foundation_score": 0.0,
    "lore_score": 0.0,
    "weakest_dimension": None,
    "layers": {
        "seed": {"status": "missing", "hash": None},
        "world": {"status": "missing", "hash": None},
        "characters": {"status": "missing", "hash": None},
        "outline": {"status": "missing", "hash": None},
        "voice": {"status": "missing", "hash": None},
        "canon": {"status": "missing", "hash": None},
        "mystery": {"status": "missing", "hash": None},
        "foreshadowing": {"status": "missing", "hash": None},
    },
    "history": [],
    "propagation_debts": [],
    "last_updated": None,
}

LAYER_FILES = {
    "seed": "seed.txt",
    "world": "world.md",
    "characters": "characters.md",
    "outline": "outline.md",
    "voice": "voice.md",
    "canon": "canon.md",
    "mystery": "MYSTERY.md",
    "foreshadowing": "foreshadowing.md",
}


class ProjectState:
    """Manages state.json for a project directory."""

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.state_path = project_dir / "state.json"
        self.data: dict[str, Any] = self._load()

    def _load(self) -> dict[str, Any]:
        if self.state_path.exists():
            return json.loads(self.state_path.read_text())
        return dict(DEFAULT_STATE)

    def save(self):
        self.data["last_updated"] = datetime.now(UTC).isoformat()
        self.state_path.write_text(json.dumps(self.data, indent=2))

    def sync_layers(self):
        """Check which layer files exist and update hashes."""
        for layer, filename in LAYER_FILES.items():
            path = self.project_dir / filename
            if path.exists():
                text = path.read_text()
                new_hash = content_hash(text)
                old_hash = self.data["layers"][layer].get("hash")
                if old_hash and old_hash != new_hash:
                    self.data["layers"][layer]["status"] = "changed"
                elif self.data["layers"][layer]["status"] == "missing":
                    self.data["layers"][layer]["status"] = "complete"
                self.data["layers"][layer]["hash"] = new_hash
            else:
                self.data["layers"][layer]["status"] = "missing"
                self.data["layers"][layer]["hash"] = None

    def update_scores(self, scores: dict):
        """Update dimension scores and compute overall/lore scores."""
        self.data["scores"].update(scores)

        # Weighted overall: lore 40%, character 30%, structure 20%, craft 10%
        s = self.data["scores"]
        lore_dims = ["world_depth"]
        char_dims = ["character_depth"]
        struct_dims = ["outline_completeness", "foreshadowing_balance"]
        craft_dims = ["internal_consistency"]

        def avg(dims):
            vals = [s.get(d, 0) for d in dims]
            return sum(vals) / len(vals) if vals else 0

        lore = avg(lore_dims)
        char = avg(char_dims)
        struct = avg(struct_dims)
        craft = avg(craft_dims)

        self.data["lore_score"] = round(lore, 2)
        self.data["foundation_score"] = round(
            lore * 0.4 + char * 0.3 + struct * 0.2 + craft * 0.1, 2
        )

        # Find weakest
        all_dims = {k: v for k, v in s.items() if isinstance(v, (int, float))}
        if all_dims:
            self.data["weakest_dimension"] = min(all_dims, key=lambda k: all_dims[k])

    def record_iteration(self, scores: dict, action: str):
        """Record an evaluation iteration in history."""
        self.data["iteration"] += 1
        self.data["history"].append(
            {
                "iteration": self.data["iteration"],
                "timestamp": datetime.now(UTC).isoformat(),
                "scores": dict(scores),
                "foundation_score": self.data["foundation_score"],
                "lore_score": self.data["lore_score"],
                "weakest_dimension": self.data["weakest_dimension"],
                "action": action,
            }
        )

    @property
    def foundation_score(self) -> float:
        return self.data.get("foundation_score", 0.0)

    @property
    def lore_score(self) -> float:
        return self.data.get("lore_score", 0.0)

    @property
    def weakest_dimension(self) -> str | None:
        return self.data.get("weakest_dimension")

    @property
    def iteration(self) -> int:
        return self.data.get("iteration", 0)

    def layer_exists(self, layer: str) -> bool:
        return self.data["layers"].get(layer, {}).get("status") != "missing"

    def missing_layers(self) -> list[str]:
        """Return list of layers that don't exist yet."""
        required = [
            "seed",
            "world",
            "characters",
            "outline",
            "voice",
            "canon",
            "mystery",
            "foreshadowing",
        ]
        return [layer for layer in required if not self.layer_exists(layer)]
