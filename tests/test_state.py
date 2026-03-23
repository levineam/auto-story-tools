"""Tests for project state management."""

import json

import pytest

from auto_outline.state import ProjectState


@pytest.fixture
def project_dir(tmp_path):
    """Create a minimal project directory."""
    (tmp_path / "seed.txt").write_text("A story about a lighthouse keeper.")
    return tmp_path


class TestProjectStateInit:
    """State initialization."""

    def test_creates_default_state(self, project_dir):
        state = ProjectState(project_dir)
        assert state.data["phase"] == "foundation"
        assert state.iteration == 0
        assert state.foundation_score == 0.0

    def test_loads_existing_state(self, project_dir):
        # Write a state file
        state_data = {
            "phase": "complete",
            "iteration": 5,
            "scores": {"world_depth": 8.0, "character_depth": 7.5},
            "foundation_score": 7.8,
            "lore_score": 8.0,
            "weakest_dimension": "character_depth",
            "layers": {},
            "history": [],
            "propagation_debts": [],
            "last_updated": None,
        }
        (project_dir / "state.json").write_text(json.dumps(state_data))

        state = ProjectState(project_dir)
        assert state.data["phase"] == "complete"
        assert state.iteration == 5
        assert state.foundation_score == 7.8


class TestLayerSync:
    """Layer file detection and hashing."""

    def test_detects_missing_layers(self, project_dir):
        state = ProjectState(project_dir)
        state.sync_layers()
        assert state.data["layers"]["world"]["status"] == "missing"

    def test_detects_existing_layers(self, project_dir):
        (project_dir / "world.md").write_text("# World\nA world of ice.")
        state = ProjectState(project_dir)
        state.sync_layers()
        assert state.data["layers"]["world"]["status"] == "complete"
        assert state.data["layers"]["world"]["hash"] is not None

    def test_detects_changed_layers(self, project_dir):
        (project_dir / "world.md").write_text("# World\nVersion 1.")
        state = ProjectState(project_dir)
        state.sync_layers()
        first_hash = state.data["layers"]["world"]["hash"]

        # Change the file
        (project_dir / "world.md").write_text("# World\nVersion 2.")
        state.sync_layers()
        assert state.data["layers"]["world"]["status"] == "changed"
        assert state.data["layers"]["world"]["hash"] != first_hash

    def test_seed_detected(self, project_dir):
        state = ProjectState(project_dir)
        state.sync_layers()
        assert state.data["layers"]["seed"]["status"] == "complete"


class TestScoring:
    """Score computation."""

    def test_update_scores(self, project_dir):
        state = ProjectState(project_dir)
        state.update_scores(
            {
                "world_depth": 8.0,
                "character_depth": 7.0,
                "outline_completeness": 6.0,
                "foreshadowing_balance": 5.0,
                "internal_consistency": 9.0,
            }
        )
        # Lore = world_depth = 8.0
        assert state.lore_score == 8.0
        # Foundation = 8.0*0.4 + 7.0*0.3 + avg(6,5)*0.2 + 9.0*0.1
        # = 3.2 + 2.1 + 1.1 + 0.9 = 7.3
        assert abs(state.foundation_score - 7.3) < 0.01
        # Weakest = foreshadowing_balance (5.0)
        assert state.weakest_dimension == "foreshadowing_balance"

    def test_missing_layers(self, project_dir):
        state = ProjectState(project_dir)
        missing = state.missing_layers()
        # Seed exists, everything else is missing
        assert "seed" not in missing
        assert "world" in missing
        assert "characters" in missing


class TestPersistence:
    """Save and reload."""

    def test_save_and_reload(self, project_dir):
        state = ProjectState(project_dir)
        state.update_scores({"world_depth": 7.5})
        state.data["iteration"] = 3
        state.save()

        reloaded = ProjectState(project_dir)
        assert reloaded.iteration == 3
        assert reloaded.data["scores"]["world_depth"] == 7.5
        assert reloaded.data["last_updated"] is not None
