"""Sample data model for tracking physical samples"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import uuid4


class SampleStatus:
    """Status constants for samples."""
    ACTIVE = "active"
    CONSUMED = "consumed"
    LOST = "lost"
    ARCHIVED = "archived"


@dataclass
class SampleLocation:
    """Where the sample is currently stored."""
    storage_type: str = ""             # wafer_box, sem_holder, tem_grid, drawer, etc.
    location_id: str = ""              # Box number, holder ID, etc.
    position: str = ""                 # Row/column, slot number if applicable
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "storage_type": self.storage_type,
            "location_id": self.location_id,
            "position": self.position,
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SampleLocation":
        return cls(
            storage_type=data.get("storage_type", ""),
            location_id=data.get("location_id", ""),
            position=data.get("position", ""),
            notes=data.get("notes", ""),
        )

    def __str__(self) -> str:
        """Human-readable location string."""
        parts = []
        if self.storage_type:
            parts.append(self.storage_type)
        if self.location_id:
            parts.append(self.location_id)
        if self.position:
            parts.append(f"pos: {self.position}")
        return " / ".join(parts) if parts else "Unknown"


@dataclass
class LocationHistoryEntry:
    """Record of a sample location change."""
    location: SampleLocation
    moved_at: str
    moved_by: str = ""
    reason: str = ""

    def to_dict(self) -> dict:
        return {
            "location": self.location.to_dict(),
            "moved_at": self.moved_at,
            "moved_by": self.moved_by,
            "reason": self.reason,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "LocationHistoryEntry":
        return cls(
            location=SampleLocation.from_dict(data.get("location", {})),
            moved_at=data.get("moved_at", ""),
            moved_by=data.get("moved_by", ""),
            reason=data.get("reason", ""),
        )


@dataclass
class Sample:
    """
    A physical sample produced from an experiment.
    One experiment can produce multiple samples (e.g., different substrate regions).
    """
    id: str = field(default_factory=lambda: str(uuid4()))
    experiment_id: str = ""            # Which experiment produced this

    # Identification
    name: str = ""                     # User-friendly name
    label: str = ""                    # Physical label on sample

    # Sample specifics
    substrate_region: str = ""         # e.g., "center", "edge", "A1"

    # Current location
    current_location: Optional[SampleLocation] = None

    # Location history
    location_history: list[LocationHistoryEntry] = field(default_factory=list)

    # Status
    status: str = SampleStatus.ACTIVE

    # Links to characterization
    characterization_ids: list[str] = field(default_factory=list)

    # Notes
    notes: str = ""

    # Timestamps
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    modified_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "experiment_id": self.experiment_id,
            "name": self.name,
            "label": self.label,
            "substrate_region": self.substrate_region,
            "current_location": self.current_location.to_dict() if self.current_location else None,
            "location_history": [entry.to_dict() for entry in self.location_history],
            "status": self.status,
            "characterization_ids": self.characterization_ids,
            "notes": self.notes,
            "created_at": self.created_at,
            "modified_at": self.modified_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Sample":
        """Create from dictionary (JSON deserialization)."""
        current_loc_data = data.get("current_location")
        current_location = SampleLocation.from_dict(current_loc_data) if current_loc_data else None

        history_data = data.get("location_history", [])
        location_history = [LocationHistoryEntry.from_dict(entry) for entry in history_data]

        return cls(
            id=data.get("id", str(uuid4())),
            experiment_id=data.get("experiment_id", ""),
            name=data.get("name", ""),
            label=data.get("label", ""),
            substrate_region=data.get("substrate_region", ""),
            current_location=current_location,
            location_history=location_history,
            status=data.get("status", SampleStatus.ACTIVE),
            characterization_ids=data.get("characterization_ids", []),
            notes=data.get("notes", ""),
            created_at=data.get("created_at", datetime.now().isoformat()),
            modified_at=data.get("modified_at", datetime.now().isoformat()),
        )

    def move_to(self, new_location: SampleLocation, moved_by: str = "", reason: str = "") -> None:
        """Move sample to a new location, recording history."""
        # Record current location in history
        if self.current_location:
            history_entry = LocationHistoryEntry(
                location=self.current_location,
                moved_at=datetime.now().isoformat(),
                moved_by=moved_by,
                reason=reason,
            )
            self.location_history.append(history_entry)

        # Update current location
        self.current_location = new_location
        self.modified_at = datetime.now().isoformat()

    def mark_consumed(self, notes: str = "") -> None:
        """Mark sample as consumed (used up)."""
        self.status = SampleStatus.CONSUMED
        if notes:
            self.notes = f"{self.notes}\nConsumed: {notes}".strip()
        self.modified_at = datetime.now().isoformat()

    def mark_lost(self, notes: str = "") -> None:
        """Mark sample as lost."""
        self.status = SampleStatus.LOST
        if notes:
            self.notes = f"{self.notes}\nLost: {notes}".strip()
        self.modified_at = datetime.now().isoformat()

    def archive(self) -> None:
        """Archive the sample."""
        self.status = SampleStatus.ARCHIVED
        self.modified_at = datetime.now().isoformat()
