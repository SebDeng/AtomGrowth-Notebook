"""Experiment data model for CVD synthesis runs"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
from uuid import uuid4


class ExperimentStatus:
    """Status constants for experiments."""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class ExperimentOutcome:
    """Outcome constants for completed experiments."""
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"
    UNKNOWN = "unknown"


@dataclass
class Experiment:
    """
    A single CVD synthesis run.

    Inherits from a template and stores only the differences (overrides).
    The resolved recipe is computed at runtime by merging
    template values with overrides.
    """
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    template_id: str = ""              # Required - which template this is based on

    # Timing
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    run_date: Optional[str] = None     # When the experiment was actually run
    completed_at: Optional[str] = None

    # Status
    status: str = ExperimentStatus.PLANNED

    # Parameter overrides (the key innovation!)
    # Stored as flat dict: {"temperature.peak_temp": 800.0, "precursor.moo3_amount": 10.0}
    overrides: dict[str, Any] = field(default_factory=dict)

    # Override reasons for documentation
    override_reasons: dict[str, str] = field(default_factory=dict)

    # Results and notes
    outcome: str = ExperimentOutcome.UNKNOWN
    notes: str = ""
    observations: str = ""

    # Links to samples produced
    sample_ids: list[str] = field(default_factory=list)

    # Links to characterization data
    characterization_ids: list[str] = field(default_factory=list)

    # Tags
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "template_id": self.template_id,
            "created_at": self.created_at,
            "run_date": self.run_date,
            "completed_at": self.completed_at,
            "status": self.status,
            "overrides": self.overrides,
            "override_reasons": self.override_reasons,
            "outcome": self.outcome,
            "notes": self.notes,
            "observations": self.observations,
            "sample_ids": self.sample_ids,
            "characterization_ids": self.characterization_ids,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Experiment":
        """Create from dictionary (JSON deserialization)."""
        return cls(
            id=data.get("id", str(uuid4())),
            name=data.get("name", ""),
            template_id=data.get("template_id", ""),
            created_at=data.get("created_at", datetime.now().isoformat()),
            run_date=data.get("run_date"),
            completed_at=data.get("completed_at"),
            status=data.get("status", ExperimentStatus.PLANNED),
            overrides=data.get("overrides", {}),
            override_reasons=data.get("override_reasons", {}),
            outcome=data.get("outcome", ExperimentOutcome.UNKNOWN),
            notes=data.get("notes", ""),
            observations=data.get("observations", ""),
            sample_ids=data.get("sample_ids", []),
            characterization_ids=data.get("characterization_ids", []),
            tags=data.get("tags", []),
        )

    def set_override(self, field_path: str, value: Any, reason: str = "") -> None:
        """Set a parameter override with optional reason."""
        self.overrides[field_path] = value
        if reason:
            self.override_reasons[field_path] = reason

    def remove_override(self, field_path: str) -> None:
        """Remove an override (revert to inherited value)."""
        self.overrides.pop(field_path, None)
        self.override_reasons.pop(field_path, None)

    def is_overridden(self, field_path: str) -> bool:
        """Check if a parameter is overridden."""
        return field_path in self.overrides

    def get_override(self, field_path: str) -> Any | None:
        """Get override value if exists, else None."""
        return self.overrides.get(field_path)

    def start_experiment(self) -> None:
        """Mark experiment as started."""
        self.status = ExperimentStatus.IN_PROGRESS
        self.run_date = datetime.now().isoformat()

    def complete_experiment(self, outcome: str = ExperimentOutcome.SUCCESS) -> None:
        """Mark experiment as completed."""
        self.status = ExperimentStatus.COMPLETED
        self.completed_at = datetime.now().isoformat()
        self.outcome = outcome

    def fail_experiment(self, notes: str = "") -> None:
        """Mark experiment as failed."""
        self.status = ExperimentStatus.FAILED
        self.completed_at = datetime.now().isoformat()
        self.outcome = ExperimentOutcome.FAILED
        if notes:
            self.notes = notes
