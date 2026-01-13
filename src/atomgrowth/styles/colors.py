"""Notion-inspired color definitions for AtomGrowth-Notebook"""


class NotionColors:
    """
    Notion-style color palette for bright/light mode.
    Clean, minimal, professional appearance.
    """

    # Primary brand color
    PRIMARY = "#2383E2"
    PRIMARY_HOVER = "#0077D4"
    PRIMARY_LIGHT = "#E8F4FD"

    # Background colors
    BACKGROUND = "#FFFFFF"
    BACKGROUND_SECONDARY = "#FBFBFA"
    BACKGROUND_TERTIARY = "#F7F6F3"
    BACKGROUND_HOVER = "#EFEFEF"

    # Text colors
    TEXT_PRIMARY = "#37352F"
    TEXT_SECONDARY = "#787774"
    TEXT_TERTIARY = "#9B9A97"
    TEXT_INVERSE = "#FFFFFF"

    # Border colors
    BORDER = "#E5E5E5"
    BORDER_LIGHT = "#EEEEEE"
    BORDER_FOCUS = "#2383E2"

    # Status colors
    SUCCESS = "#0F7B6C"
    SUCCESS_BG = "#DBEDDB"
    WARNING = "#D9730D"
    WARNING_BG = "#FAEBDD"
    ERROR = "#E03E3E"
    ERROR_BG = "#FBE4E4"
    INFO = "#2383E2"
    INFO_BG = "#E8F4FD"

    # Shadows
    SHADOW_LIGHT = "rgba(15, 15, 15, 0.04)"
    SHADOW_MEDIUM = "rgba(15, 15, 15, 0.1)"

    # Sidebar specific
    SIDEBAR_BG = "#FBFBFA"
    SIDEBAR_ITEM_HOVER = "#EFEFEF"
    SIDEBAR_ITEM_SELECTED = "#E8F4FD"

    # ===== AtomGrowth-Notebook Specific Colors =====

    # Template inheritance indicators
    INHERITED = "#9B9A97"              # Gray for inherited values
    INHERITED_BG = "#F7F6F3"
    OVERRIDDEN = "#2383E2"             # Blue for overridden values
    OVERRIDDEN_BG = "#E8F4FD"

    # Experiment status colors
    STATUS_PLANNED = "#787774"
    STATUS_PLANNED_BG = "#F7F6F3"
    STATUS_IN_PROGRESS = "#D9730D"
    STATUS_IN_PROGRESS_BG = "#FAEBDD"
    STATUS_COMPLETED = "#0F7B6C"
    STATUS_COMPLETED_BG = "#DBEDDB"
    STATUS_FAILED = "#E03E3E"
    STATUS_FAILED_BG = "#FBE4E4"

    # Sample location colors
    LOCATION_ACTIVE = "#0F7B6C"
    LOCATION_CONSUMED = "#9B9A97"
    LOCATION_LOST = "#E03E3E"

    # CVD parameter section colors (for visual grouping)
    SECTION_TEMPERATURE = "#EB5757"
    SECTION_TEMPERATURE_BG = "#FBE4E4"
    SECTION_GAS_FLOW = "#2383E2"
    SECTION_GAS_FLOW_BG = "#E8F4FD"
    SECTION_PRECURSOR = "#0F7B6C"
    SECTION_PRECURSOR_BG = "#DBEDDB"
    SECTION_SUBSTRATE = "#9B59B6"
    SECTION_SUBSTRATE_BG = "#F3E5F5"
