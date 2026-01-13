"""Application-wide signals for cross-component communication"""

from PySide6.QtCore import QObject, Signal


class AppSignals(QObject):
    """
    Singleton class containing all application-wide signals.
    Use get_app_signals() to access the instance.
    """

    _instance = None

    # ===== Template signals =====
    template_created = Signal(str)           # template_id
    template_modified = Signal(str)
    template_deleted = Signal(str)
    template_selected = Signal(str)          # template_id

    # ===== Experiment signals =====
    experiment_created = Signal(str)         # experiment_id
    experiment_modified = Signal(str)
    experiment_deleted = Signal(str)
    experiment_selected = Signal(str)
    experiment_status_changed = Signal(str, str)  # (id, new_status)

    # ===== Sample signals =====
    sample_created = Signal(str)             # sample_id
    sample_modified = Signal(str)
    sample_deleted = Signal(str)
    sample_selected = Signal(str)
    sample_location_changed = Signal(str, str)    # (sample_id, new_location_id)

    # ===== Characterization signals =====
    characterization_added = Signal(str, str)     # (entity_type, entity_id)
    characterization_deleted = Signal(str)
    characterization_selected = Signal(str)

    # ===== Project signals =====
    project_opened = Signal(str)             # project_path
    project_closed = Signal()
    project_modified = Signal()
    project_saved = Signal()

    # ===== Navigation signals =====
    navigation_changed = Signal(str)         # view_name: "templates", "experiments", "samples", "gallery"
    search_query_changed = Signal(str)       # search text

    # ===== UI signals =====
    status_message = Signal(str, int)        # (message, timeout_ms)
    busy_state_changed = Signal(bool)

    def __init__(self):
        # Only initialize once
        if not hasattr(self, '_initialized'):
            super().__init__()
            self._initialized = True


# Module-level singleton instance
_app_signals_instance: AppSignals | None = None


def get_app_signals() -> AppSignals:
    """Get the singleton AppSignals instance"""
    global _app_signals_instance
    if _app_signals_instance is None:
        _app_signals_instance = AppSignals()
    return _app_signals_instance
