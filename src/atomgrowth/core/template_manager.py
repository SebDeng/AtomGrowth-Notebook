"""Template manager for CRUD operations and inheritance resolution"""

import json
import copy
from pathlib import Path
from typing import Any, Optional
from dataclasses import fields, is_dataclass

from atomgrowth.models.recipe import (
    RecipeTemplate, TemperatureProfile, GasFlow, PrecursorSetup, SubstrateInfo
)
from atomgrowth.signals.app_signals import get_app_signals


class TemplateManager:
    """
    Manages recipe templates with inheritance resolution.

    Key features:
    - CRUD operations for templates
    - Multi-level inheritance resolution
    - Field path access (e.g., "temperature.peak_temp")
    - Diff generation between templates
    """

    def __init__(self, storage_path: Optional[Path] = None):
        self._templates: dict[str, RecipeTemplate] = {}
        self._storage_path = storage_path
        self._signals = get_app_signals()

        if storage_path and storage_path.exists():
            self.load()

    # ==================== CRUD Operations ====================

    def create_template(
        self,
        name: str,
        parent_id: Optional[str] = None,
        description: str = ""
    ) -> RecipeTemplate:
        """Create a new template, optionally inheriting from parent."""
        template = RecipeTemplate(name=name, description=description)

        if parent_id:
            if parent_id not in self._templates:
                raise ValueError(f"Parent template '{parent_id}' not found")
            if self._would_create_cycle(template.id, parent_id):
                raise ValueError("Cannot create circular inheritance")
            template.parent_template_id = parent_id

        self._templates[template.id] = template
        self._signals.template_created.emit(template.id)
        return template

    def get_template(self, template_id: str) -> Optional[RecipeTemplate]:
        """Get a template by ID."""
        return self._templates.get(template_id)

    def update_template(self, template: RecipeTemplate) -> None:
        """Update an existing template."""
        if template.id not in self._templates:
            raise ValueError(f"Template '{template.id}' not found")

        template.update_modified()
        self._templates[template.id] = template
        self._signals.template_modified.emit(template.id)

    def delete_template(self, template_id: str) -> bool:
        """Delete a template. Returns False if template has children."""
        if template_id not in self._templates:
            return False

        # Check if any templates inherit from this one
        for t in self._templates.values():
            if t.parent_template_id == template_id:
                raise ValueError(
                    f"Cannot delete: template '{t.name}' inherits from this template"
                )

        del self._templates[template_id]
        self._signals.template_deleted.emit(template_id)
        return True

    def list_templates(self) -> list[RecipeTemplate]:
        """List all templates."""
        return list(self._templates.values())

    def get_root_templates(self) -> list[RecipeTemplate]:
        """Get templates with no parent (root templates)."""
        return [t for t in self._templates.values() if t.parent_template_id is None]

    def get_children(self, template_id: str) -> list[RecipeTemplate]:
        """Get templates that directly inherit from the given template."""
        return [
            t for t in self._templates.values()
            if t.parent_template_id == template_id
        ]

    # ==================== Inheritance Resolution ====================

    def resolve_template(self, template_id: str) -> RecipeTemplate:
        """
        Resolve full template by walking inheritance chain.
        Returns a fully populated RecipeTemplate with all values resolved.
        """
        if template_id not in self._templates:
            raise ValueError(f"Template '{template_id}' not found")

        chain = self.get_inheritance_chain(template_id)

        # Start with default values
        resolved = RecipeTemplate(
            id=template_id,
            name=self._templates[template_id].name
        )

        # Apply templates from root to leaf (earliest ancestor first)
        for template in reversed(chain):
            resolved = self._merge_templates(resolved, template)

        return resolved

    def get_inheritance_chain(self, template_id: str) -> list[RecipeTemplate]:
        """
        Return the full inheritance chain for a template.
        Order: [template, parent, grandparent, ..., root]
        """
        chain = []
        current_id = template_id
        visited = set()

        while current_id:
            if current_id in visited:
                raise ValueError("Circular inheritance detected")
            visited.add(current_id)

            template = self._templates.get(current_id)
            if not template:
                break

            chain.append(template)
            current_id = template.parent_template_id

        return chain

    def get_effective_value(
        self,
        template_id: str,
        field_path: str
    ) -> tuple[Any, Optional[str]]:
        """
        Get the effective value for a field and which template it came from.

        Returns: (value, source_template_id)
        - source_template_id is None if using default value
        """
        chain = self.get_inheritance_chain(template_id)

        # Walk from current template up to root
        for template in chain:
            value = self._get_field_value(template, field_path)
            # Check if this template explicitly sets this value
            # (For now, we assume any non-None value is explicit)
            if value is not None:
                return (value, template.id)

        # Return default value
        default_template = RecipeTemplate()
        default_value = self._get_field_value(default_template, field_path)
        return (default_value, None)

    # ==================== Field Path Access ====================

    @staticmethod
    def _get_field_value(obj: Any, path: str) -> Any:
        """
        Get a nested field value using dot notation.
        e.g., "temperature.peak_temp" -> obj.temperature.peak_temp
        """
        parts = path.split('.')
        current = obj

        for part in parts:
            if current is None:
                return None
            if hasattr(current, part):
                current = getattr(current, part)
            elif isinstance(current, dict):
                current = current.get(part)
            else:
                return None

        return current

    @staticmethod
    def _set_field_value(obj: Any, path: str, value: Any) -> bool:
        """
        Set a nested field value using dot notation.
        Returns True if successful.
        """
        parts = path.split('.')
        current = obj

        # Navigate to the parent of the target field
        for part in parts[:-1]:
            if hasattr(current, part):
                current = getattr(current, part)
            elif isinstance(current, dict):
                if part not in current:
                    current[part] = {}
                current = current[part]
            else:
                return False

        # Set the final field
        final_part = parts[-1]
        if hasattr(current, final_part):
            setattr(current, final_part, value)
            return True
        elif isinstance(current, dict):
            current[final_part] = value
            return True

        return False

    def get_all_field_paths(self) -> list[str]:
        """Get all available field paths for a template."""
        paths = []

        # Temperature fields
        for f in fields(TemperatureProfile):
            paths.append(f"temperature.{f.name}")

        # Gas flow fields
        for f in fields(GasFlow):
            paths.append(f"gas_flow.{f.name}")

        # Precursor fields
        for f in fields(PrecursorSetup):
            paths.append(f"precursor.{f.name}")

        # Substrate fields
        for f in fields(SubstrateInfo):
            paths.append(f"substrate.{f.name}")

        return paths

    # ==================== Merge & Diff ====================

    def _merge_templates(
        self,
        base: RecipeTemplate,
        overlay: RecipeTemplate
    ) -> RecipeTemplate:
        """
        Deep merge overlay onto base. Overlay values win.
        """
        result = copy.deepcopy(base)

        # Merge each section
        result.temperature = self._merge_dataclass(
            result.temperature, overlay.temperature
        )
        result.gas_flow = self._merge_dataclass(
            result.gas_flow, overlay.gas_flow
        )
        result.precursor = self._merge_dataclass(
            result.precursor, overlay.precursor
        )
        result.substrate = self._merge_dataclass(
            result.substrate, overlay.substrate
        )

        # Merge custom fields (overlay wins)
        result.custom_fields.update(overlay.custom_fields)

        # Merge tags (union)
        result.tags = list(set(result.tags) | set(overlay.tags))

        # Keep overlay's metadata
        result.name = overlay.name
        result.description = overlay.description or result.description
        result.parent_template_id = overlay.parent_template_id
        result.created_at = overlay.created_at
        result.modified_at = overlay.modified_at

        return result

    @staticmethod
    def _merge_dataclass(base: Any, overlay: Any) -> Any:
        """Merge two dataclass instances. Non-default overlay values win."""
        if not is_dataclass(base) or not is_dataclass(overlay):
            return overlay if overlay is not None else base

        result = copy.deepcopy(base)

        for field in fields(overlay):
            overlay_value = getattr(overlay, field.name)
            # Always use overlay value (could add smarter default detection)
            setattr(result, field.name, overlay_value)

        return result

    def diff_templates(
        self,
        template_id_1: str,
        template_id_2: str
    ) -> list[dict]:
        """
        Compare two templates and return differences.

        Returns list of dicts:
        [{"field_path": "...", "value_1": ..., "value_2": ...}, ...]
        """
        t1 = self.resolve_template(template_id_1)
        t2 = self.resolve_template(template_id_2)

        diffs = []
        for path in self.get_all_field_paths():
            v1 = self._get_field_value(t1, path)
            v2 = self._get_field_value(t2, path)

            if v1 != v2:
                diffs.append({
                    "field_path": path,
                    "value_1": v1,
                    "value_2": v2,
                })

        return diffs

    # ==================== Cycle Detection ====================

    def _would_create_cycle(self, template_id: str, new_parent_id: str) -> bool:
        """Check if setting new_parent_id would create a circular reference."""
        visited = {template_id}
        current_id = new_parent_id

        while current_id:
            if current_id in visited:
                return True
            visited.add(current_id)

            template = self._templates.get(current_id)
            if not template:
                break
            current_id = template.parent_template_id

        return False

    # ==================== Persistence ====================

    def save(self, path: Optional[Path] = None) -> None:
        """Save all templates to JSON file."""
        save_path = path or self._storage_path
        if not save_path:
            raise ValueError("No storage path specified")

        save_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "version": 1,
            "templates": {
                tid: t.to_dict() for tid, t in self._templates.items()
            }
        }

        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    def load(self, path: Optional[Path] = None) -> None:
        """Load templates from JSON file."""
        load_path = path or self._storage_path
        if not load_path or not load_path.exists():
            return

        with open(load_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self._templates = {}
        for tid, tdata in data.get("templates", {}).items():
            self._templates[tid] = RecipeTemplate.from_dict(tdata)
