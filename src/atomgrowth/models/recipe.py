"""Recipe and Template data models for CVD synthesis"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
from uuid import uuid4


@dataclass
class TemperatureProfile:
    """Temperature profile for CVD synthesis."""
    ramp_rate_1: float = 10.0          # C/min to first hold
    hold_temp_1: float = 300.0         # C - first hold temperature
    hold_time_1: float = 10.0          # minutes
    ramp_rate_2: float = 5.0           # C/min to peak
    peak_temp: float = 750.0           # C - peak temperature
    peak_hold_time: float = 15.0       # minutes
    cooling_method: str = "natural"    # natural, controlled, quench
    controlled_cool_rate: float = 10.0 # C/min if controlled


@dataclass
class GasFlow:
    """Gas flow parameters."""
    ar_flow: float = 100.0             # sccm - Argon flow
    h2_flow: float = 0.0               # sccm - Hydrogen flow (optional)
    total_flow: float = 100.0          # sccm - Total flow


@dataclass
class PrecursorSetup:
    """Precursor configuration for MoS2 CVD."""
    moo3_amount: float = 5.0           # mg - MoO3 precursor amount
    s_amount: float = 100.0            # mg - Sulfur amount
    moo3_position: float = 0.0         # cm from center (positive = downstream)
    s_position: float = -15.0          # cm from center (negative = upstream)
    moo3_boat_material: str = "alumina"
    s_boat_material: str = "quartz"


@dataclass
class SubstrateInfo:
    """Substrate details."""
    material: str = "SiO2/Si"
    oxide_thickness: float = 300.0     # nm - oxide layer thickness
    prep_method: str = "piranha"       # piranha, O2_plasma, acetone_IPA, sonication
    orientation: str = "(100)"
    size: str = "1cm x 1cm"


@dataclass
class RecipeTemplate:
    """
    Base recipe template that can be inherited.

    Key concept: Templates store EXPLICIT values.
    Experiments inherit from templates and only store OVERRIDES.
    """
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    description: str = ""
    parent_template_id: Optional[str] = None  # For template inheritance

    # Creation metadata
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    modified_at: str = field(default_factory=lambda: datetime.now().isoformat())

    # Recipe parameters (all have defaults)
    temperature: TemperatureProfile = field(default_factory=TemperatureProfile)
    gas_flow: GasFlow = field(default_factory=GasFlow)
    precursor: PrecursorSetup = field(default_factory=PrecursorSetup)
    substrate: SubstrateInfo = field(default_factory=SubstrateInfo)

    # Custom fields for extensibility
    custom_fields: dict[str, Any] = field(default_factory=dict)

    # Tags for organization
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "parent_template_id": self.parent_template_id,
            "created_at": self.created_at,
            "modified_at": self.modified_at,
            "temperature": {
                "ramp_rate_1": self.temperature.ramp_rate_1,
                "hold_temp_1": self.temperature.hold_temp_1,
                "hold_time_1": self.temperature.hold_time_1,
                "ramp_rate_2": self.temperature.ramp_rate_2,
                "peak_temp": self.temperature.peak_temp,
                "peak_hold_time": self.temperature.peak_hold_time,
                "cooling_method": self.temperature.cooling_method,
                "controlled_cool_rate": self.temperature.controlled_cool_rate,
            },
            "gas_flow": {
                "ar_flow": self.gas_flow.ar_flow,
                "h2_flow": self.gas_flow.h2_flow,
                "total_flow": self.gas_flow.total_flow,
            },
            "precursor": {
                "moo3_amount": self.precursor.moo3_amount,
                "s_amount": self.precursor.s_amount,
                "moo3_position": self.precursor.moo3_position,
                "s_position": self.precursor.s_position,
                "moo3_boat_material": self.precursor.moo3_boat_material,
                "s_boat_material": self.precursor.s_boat_material,
            },
            "substrate": {
                "material": self.substrate.material,
                "oxide_thickness": self.substrate.oxide_thickness,
                "prep_method": self.substrate.prep_method,
                "orientation": self.substrate.orientation,
                "size": self.substrate.size,
            },
            "custom_fields": self.custom_fields,
            "tags": self.tags,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RecipeTemplate":
        """Create from dictionary (JSON deserialization)."""
        temp_data = data.get("temperature", {})
        gas_data = data.get("gas_flow", {})
        precursor_data = data.get("precursor", {})
        substrate_data = data.get("substrate", {})

        return cls(
            id=data.get("id", str(uuid4())),
            name=data.get("name", ""),
            description=data.get("description", ""),
            parent_template_id=data.get("parent_template_id"),
            created_at=data.get("created_at", datetime.now().isoformat()),
            modified_at=data.get("modified_at", datetime.now().isoformat()),
            temperature=TemperatureProfile(
                ramp_rate_1=temp_data.get("ramp_rate_1", 10.0),
                hold_temp_1=temp_data.get("hold_temp_1", 300.0),
                hold_time_1=temp_data.get("hold_time_1", 10.0),
                ramp_rate_2=temp_data.get("ramp_rate_2", 5.0),
                peak_temp=temp_data.get("peak_temp", 750.0),
                peak_hold_time=temp_data.get("peak_hold_time", 15.0),
                cooling_method=temp_data.get("cooling_method", "natural"),
                controlled_cool_rate=temp_data.get("controlled_cool_rate", 10.0),
            ),
            gas_flow=GasFlow(
                ar_flow=gas_data.get("ar_flow", 100.0),
                h2_flow=gas_data.get("h2_flow", 0.0),
                total_flow=gas_data.get("total_flow", 100.0),
            ),
            precursor=PrecursorSetup(
                moo3_amount=precursor_data.get("moo3_amount", 5.0),
                s_amount=precursor_data.get("s_amount", 100.0),
                moo3_position=precursor_data.get("moo3_position", 0.0),
                s_position=precursor_data.get("s_position", -15.0),
                moo3_boat_material=precursor_data.get("moo3_boat_material", "alumina"),
                s_boat_material=precursor_data.get("s_boat_material", "quartz"),
            ),
            substrate=SubstrateInfo(
                material=substrate_data.get("material", "SiO2/Si"),
                oxide_thickness=substrate_data.get("oxide_thickness", 300.0),
                prep_method=substrate_data.get("prep_method", "piranha"),
                orientation=substrate_data.get("orientation", "(100)"),
                size=substrate_data.get("size", "1cm x 1cm"),
            ),
            custom_fields=data.get("custom_fields", {}),
            tags=data.get("tags", []),
        )

    def update_modified(self) -> None:
        """Update the modified timestamp."""
        self.modified_at = datetime.now().isoformat()
