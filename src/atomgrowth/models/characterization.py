"""Characterization data model for images and spectra"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
from uuid import uuid4


class CharacterizationType:
    """Type constants for characterization data."""
    OPTICAL_IMAGE = "optical_image"
    RAMAN_SPECTRUM = "raman_spectrum"
    SEM = "sem"
    TEM = "tem"
    AFM = "afm"
    PL = "pl"  # Photoluminescence
    XPS = "xps"
    OTHER = "other"


@dataclass
class CharacterizationData:
    """
    Characterization data linked to samples or experiments.
    Supports optical images, Raman spectra, and extensible data types.
    """
    id: str = field(default_factory=lambda: str(uuid4()))

    # Links (at least one should be set)
    sample_id: Optional[str] = None
    experiment_id: Optional[str] = None

    # Type
    data_type: str = CharacterizationType.OTHER

    # File reference
    file_path: str = ""                # Relative path within project
    file_name: str = ""
    file_size: int = 0                 # bytes

    # Type-specific metadata (flexible dict)
    # For optical: {"magnification": "50x", "microscope": "Olympus BX51", "filter": "none"}
    # For Raman: {"wavelength": 532, "power_mw": 1.0, "integration_time_s": 10, "accumulations": 3}
    # For SEM: {"voltage_kv": 5, "magnification": "10000x", "detector": "SE"}
    metadata: dict[str, Any] = field(default_factory=dict)

    # Acquisition info
    acquired_at: str = ""
    acquired_by: str = ""
    instrument: str = ""

    # Notes and annotations
    notes: str = ""
    annotations: list[dict] = field(default_factory=list)  # For image annotations

    # Timestamps
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    modified_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "sample_id": self.sample_id,
            "experiment_id": self.experiment_id,
            "data_type": self.data_type,
            "file_path": self.file_path,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "metadata": self.metadata,
            "acquired_at": self.acquired_at,
            "acquired_by": self.acquired_by,
            "instrument": self.instrument,
            "notes": self.notes,
            "annotations": self.annotations,
            "created_at": self.created_at,
            "modified_at": self.modified_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CharacterizationData":
        """Create from dictionary (JSON deserialization)."""
        return cls(
            id=data.get("id", str(uuid4())),
            sample_id=data.get("sample_id"),
            experiment_id=data.get("experiment_id"),
            data_type=data.get("data_type", CharacterizationType.OTHER),
            file_path=data.get("file_path", ""),
            file_name=data.get("file_name", ""),
            file_size=data.get("file_size", 0),
            metadata=data.get("metadata", {}),
            acquired_at=data.get("acquired_at", ""),
            acquired_by=data.get("acquired_by", ""),
            instrument=data.get("instrument", ""),
            notes=data.get("notes", ""),
            annotations=data.get("annotations", []),
            created_at=data.get("created_at", datetime.now().isoformat()),
            modified_at=data.get("modified_at", datetime.now().isoformat()),
        )

    def update_modified(self) -> None:
        """Update the modified timestamp."""
        self.modified_at = datetime.now().isoformat()


@dataclass
class RamanData(CharacterizationData):
    """
    Extended schema for Raman spectra with extracted peak information.
    """
    # Extracted peak data for MoS2
    e2g_position: Optional[float] = None    # cm^-1 - E2g peak position
    a1g_position: Optional[float] = None    # cm^-1 - A1g peak position
    peak_separation: Optional[float] = None  # cm^-1 - A1g - E2g (layer indicator)
    e2g_intensity: Optional[float] = None
    a1g_intensity: Optional[float] = None
    e2g_fwhm: Optional[float] = None        # Full width at half maximum
    a1g_fwhm: Optional[float] = None
    layer_count_estimate: Optional[int] = None  # Estimated layer count from separation

    def __post_init__(self):
        # Ensure data_type is set correctly
        self.data_type = CharacterizationType.RAMAN_SPECTRUM

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        base = super().to_dict()
        base.update({
            "e2g_position": self.e2g_position,
            "a1g_position": self.a1g_position,
            "peak_separation": self.peak_separation,
            "e2g_intensity": self.e2g_intensity,
            "a1g_intensity": self.a1g_intensity,
            "e2g_fwhm": self.e2g_fwhm,
            "a1g_fwhm": self.a1g_fwhm,
            "layer_count_estimate": self.layer_count_estimate,
        })
        return base

    @classmethod
    def from_dict(cls, data: dict) -> "RamanData":
        """Create from dictionary (JSON deserialization)."""
        return cls(
            id=data.get("id", str(uuid4())),
            sample_id=data.get("sample_id"),
            experiment_id=data.get("experiment_id"),
            data_type=CharacterizationType.RAMAN_SPECTRUM,
            file_path=data.get("file_path", ""),
            file_name=data.get("file_name", ""),
            file_size=data.get("file_size", 0),
            metadata=data.get("metadata", {}),
            acquired_at=data.get("acquired_at", ""),
            acquired_by=data.get("acquired_by", ""),
            instrument=data.get("instrument", ""),
            notes=data.get("notes", ""),
            annotations=data.get("annotations", []),
            created_at=data.get("created_at", datetime.now().isoformat()),
            modified_at=data.get("modified_at", datetime.now().isoformat()),
            e2g_position=data.get("e2g_position"),
            a1g_position=data.get("a1g_position"),
            peak_separation=data.get("peak_separation"),
            e2g_intensity=data.get("e2g_intensity"),
            a1g_intensity=data.get("a1g_intensity"),
            e2g_fwhm=data.get("e2g_fwhm"),
            a1g_fwhm=data.get("a1g_fwhm"),
            layer_count_estimate=data.get("layer_count_estimate"),
        )

    def calculate_peak_separation(self) -> None:
        """Calculate peak separation from positions."""
        if self.e2g_position is not None and self.a1g_position is not None:
            self.peak_separation = self.a1g_position - self.e2g_position

    def estimate_layers(self) -> None:
        """
        Estimate layer count from peak separation.
        Typical values for MoS2:
        - Monolayer: ~18-19 cm^-1
        - Bilayer: ~21-22 cm^-1
        - Trilayer: ~23 cm^-1
        - Bulk: ~25 cm^-1
        """
        if self.peak_separation is None:
            self.calculate_peak_separation()

        if self.peak_separation is not None:
            sep = self.peak_separation
            if sep < 20:
                self.layer_count_estimate = 1
            elif sep < 22:
                self.layer_count_estimate = 2
            elif sep < 24:
                self.layer_count_estimate = 3
            else:
                self.layer_count_estimate = 4  # 4+ means bulk-like
