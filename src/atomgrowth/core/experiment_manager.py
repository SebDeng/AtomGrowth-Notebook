"""Experiment manager for CRUD operations and image management"""

import json
import shutil
from pathlib import Path
from typing import Optional
from datetime import datetime

from atomgrowth.models.experiment import Experiment
from atomgrowth.signals.app_signals import get_app_signals


class ExperimentManager:
    """
    Manages experiments with image file handling.

    Key features:
    - CRUD operations for experiments
    - Image file copying to app data directory
    - Integration with TemplateManager for parameter resolution
    """

    def __init__(
        self,
        storage_path: Optional[Path] = None,
        images_dir: Optional[Path] = None
    ):
        self._experiments: dict[str, Experiment] = {}
        self._storage_path = storage_path
        self._images_dir = images_dir
        self._signals = get_app_signals()

        # Create images directory if needed
        if images_dir:
            images_dir.mkdir(parents=True, exist_ok=True)

        if storage_path and storage_path.exists():
            self.load()

    # ==================== CRUD Operations ====================

    def create_experiment(
        self,
        name: str,
        template_id: str,
        notes: str = ""
    ) -> Experiment:
        """Create a new experiment based on a template."""
        experiment = Experiment(
            name=name,
            template_id=template_id,
            notes=notes,
            run_date=datetime.now().isoformat()
        )

        self._experiments[experiment.id] = experiment
        self._signals.experiment_created.emit(experiment.id)
        return experiment

    def get_experiment(self, experiment_id: str) -> Optional[Experiment]:
        """Get an experiment by ID."""
        return self._experiments.get(experiment_id)

    def update_experiment(self, experiment: Experiment) -> None:
        """Update an existing experiment."""
        if experiment.id not in self._experiments:
            raise ValueError(f"Experiment '{experiment.id}' not found")

        self._experiments[experiment.id] = experiment
        self._signals.experiment_modified.emit(experiment.id)

    def delete_experiment(self, experiment_id: str) -> bool:
        """Delete an experiment and its associated images."""
        if experiment_id not in self._experiments:
            return False

        experiment = self._experiments[experiment_id]

        # Delete associated image files
        if self._images_dir:
            for image_path in experiment.optical_images:
                full_path = self._images_dir / image_path
                if full_path.exists():
                    full_path.unlink()

        del self._experiments[experiment_id]
        self._signals.experiment_deleted.emit(experiment_id)
        return True

    def list_experiments(self) -> list[Experiment]:
        """List all experiments."""
        return list(self._experiments.values())

    def list_experiments_by_date(self) -> list[Experiment]:
        """List experiments sorted by date (newest first)."""
        experiments = list(self._experiments.values())
        return sorted(
            experiments,
            key=lambda e: e.created_at,
            reverse=True
        )

    def list_experiments_by_template(self) -> dict[str, list[Experiment]]:
        """Group experiments by template ID."""
        grouped: dict[str, list[Experiment]] = {}
        for exp in self._experiments.values():
            if exp.template_id not in grouped:
                grouped[exp.template_id] = []
            grouped[exp.template_id].append(exp)

        # Sort each group by date
        for template_id in grouped:
            grouped[template_id].sort(key=lambda e: e.created_at, reverse=True)

        return grouped

    # ==================== Image Management ====================

    def add_image_to_experiment(
        self,
        experiment_id: str,
        source_path: Path
    ) -> Optional[str]:
        """
        Copy an image file to the app directory and add to experiment.
        Returns the relative path of the copied image, or None if failed.
        """
        experiment = self.get_experiment(experiment_id)
        if not experiment:
            return None

        if not self._images_dir:
            raise ValueError("Images directory not configured")

        if not source_path.exists():
            raise FileNotFoundError(f"Source image not found: {source_path}")

        # Create experiment subdirectory
        exp_images_dir = self._images_dir / experiment_id
        exp_images_dir.mkdir(parents=True, exist_ok=True)

        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest_filename = f"{timestamp}_{source_path.name}"
        dest_path = exp_images_dir / dest_filename

        # Copy the file
        shutil.copy2(source_path, dest_path)

        # Store relative path (from images_dir)
        relative_path = f"{experiment_id}/{dest_filename}"
        experiment.add_optical_image(relative_path)

        self._signals.experiment_modified.emit(experiment_id)
        return relative_path

    def remove_image_from_experiment(
        self,
        experiment_id: str,
        image_path: str
    ) -> bool:
        """Remove an image from experiment and delete the file."""
        experiment = self.get_experiment(experiment_id)
        if not experiment:
            return False

        if image_path not in experiment.optical_images:
            return False

        # Delete the file
        if self._images_dir:
            full_path = self._images_dir / image_path
            if full_path.exists():
                full_path.unlink()

        experiment.remove_optical_image(image_path)
        self._signals.experiment_modified.emit(experiment_id)
        return True

    def get_image_full_path(self, image_path: str) -> Optional[Path]:
        """Get the full filesystem path for an image."""
        if not self._images_dir:
            return None
        return self._images_dir / image_path

    # ==================== Raman File Management ====================

    def add_raman_to_experiment(
        self,
        experiment_id: str,
        source_path: Path
    ) -> Optional[str]:
        """
        Copy a Raman file to the app directory and add to experiment.
        Returns the relative path of the copied file, or None if failed.
        """
        experiment = self.get_experiment(experiment_id)
        if not experiment:
            return None

        if not self._images_dir:
            raise ValueError("Data directory not configured")

        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {source_path}")

        # Create experiment subdirectory for raman
        exp_raman_dir = self._images_dir / experiment_id / "raman"
        exp_raman_dir.mkdir(parents=True, exist_ok=True)

        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest_filename = f"{timestamp}_{source_path.name}"
        dest_path = exp_raman_dir / dest_filename

        # Copy the file
        shutil.copy2(source_path, dest_path)

        # Store relative path
        relative_path = f"{experiment_id}/raman/{dest_filename}"
        experiment.add_raman_file(relative_path)

        self._signals.experiment_modified.emit(experiment_id)
        return relative_path

    def remove_raman_from_experiment(
        self,
        experiment_id: str,
        file_path: str
    ) -> bool:
        """Remove a Raman file from experiment and delete the file."""
        experiment = self.get_experiment(experiment_id)
        if not experiment:
            return False

        if file_path not in experiment.raman_files:
            return False

        # Delete the file
        if self._images_dir:
            full_path = self._images_dir / file_path
            if full_path.exists():
                full_path.unlink()

        experiment.remove_raman_file(file_path)
        self._signals.experiment_modified.emit(experiment_id)
        return True

    # ==================== Persistence ====================

    def save(self, path: Optional[Path] = None) -> None:
        """Save all experiments to JSON file."""
        save_path = path or self._storage_path
        if not save_path:
            raise ValueError("No storage path specified")

        save_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "version": 1,
            "experiments": {
                eid: e.to_dict() for eid, e in self._experiments.items()
            }
        }

        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load(self, path: Optional[Path] = None) -> None:
        """Load experiments from JSON file."""
        load_path = path or self._storage_path
        if not load_path or not load_path.exists():
            return

        with open(load_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self._experiments = {}
        for eid, edata in data.get("experiments", {}).items():
            self._experiments[eid] = Experiment.from_dict(edata)
