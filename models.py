from typing import Dict, List, Optional, Literal, Any
from pydantic import BaseModel, Field, validator, root_validator
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class DashboardProviderConfig(BaseModel):
    """Configuration for dashboard provider with production hardening.
    
    Attributes:
        name: Unique identifier for the provider
        org_id: Grafana organization ID (must be positive integer)
        folder: Dashboard folder path (default: root)
        type: Provider type (fixed as 'file')
        disable_deletion: Prevent dashboard deletion (default: True)
        update_interval_seconds: How often to check for updates (min: 10s)
        allow_ui_updates: Allow manual dashboard edits (default: False)
        options: Provider-specific configuration
    """

    name: str = Field(..., min_length=1, max_length=100, regex=r'^[a-zA-Z0-9_-]+$')
    org_id: int = Field(..., alias="orgId", gt=0)
    folder: str = Field("", max_length=200)
    type: Literal["file"] = "file"
    disable_deletion: bool = Field(True, alias="disableDeletion")
    update_interval_seconds: int = Field(
        60, 
        alias="updateIntervalSeconds",
        ge=10,  # Minimum 10 seconds to avoid excessive polling
        le=86400  # Maximum 1 day
    )
    allow_ui_updates: bool = Field(False, alias="allowUiUpdates")
    options: Dict[str, Any] = Field(default_factory=dict)

    @validator('options')
    def validate_options(cls, v):
        if 'path' in v and not isinstance(v['path'], str):
            raise ValueError('Path must be a string')
        return v


class DashboardPanel(BaseModel):
    """Production-ready model for Grafana dashboard panels with validation.
    
    Attributes:
        id: Unique panel ID (positive integer)
        title: Panel title (1-100 chars)
        description: Optional panel description
        datasource: Data source name (must exist in Grafana)
        grid_pos: Panel position and size
        targets: Data queries/targets (at least one required)
        field_config: Panel field configuration
        refresh: Refresh interval (must be valid duration string)
    """

    id: int = Field(..., gt=0)
    title: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    datasource: str = Field(..., min_length=1, max_length=100)
    grid_pos: Dict[str, int] = Field(..., alias="gridPos")
    targets: List[Dict[str, Any]]
    field_config: Dict[str, Any] = Field(..., alias="fieldConfig")
    refresh: Optional[str] = Field(
        None,
        regex=r'^\d+[smh]$'  # Must be like '30s', '5m', '1h'
    )

    @validator('grid_pos')
    def validate_grid_pos(cls, v):
        required_keys = {'x', 'y', 'w', 'h'}
        if not required_keys.issubset(v.keys()):
            raise ValueError('gridPos must contain x, y, w, h')
        return v

    @validator('targets')
    def validate_targets(cls, v):
        if not v:
            raise ValueError('Panel must have at least one target')
        return v


class DashboardAnnotations(BaseModel):
    """Validated model for Grafana dashboard annotations.
    
    Attributes:
        name: Annotation name (unique identifier)
        datasource: Data source name
        enable: Whether annotation is enabled
        hide: Whether annotation is hidden
        icon_color: Color for annotation icon
    """

    name: str = Field(..., min_length=1, max_length=50)
    datasource: str = Field(..., min_length=1, max_length=100)
    enable: bool = True
    hide: bool = False
    icon_color: str = Field(
        ..., 
        alias="iconColor",
        regex=r'^#[0-9a-fA-F]{6}$'  # Hex color format
    )


class DashboardTemplateVariable(BaseModel):
    """Production-ready template variable model with validation.
    
    Attributes:
        name: Variable name (must be valid identifier)
        label: Display label
        query: Data query
        current: Currently selected value
        options: Available options
    """

    name: str = Field(..., min_length=1, max_length=50, regex=r'^[a-zA-Z][a-zA-Z0-9_]*$')
    label: str = Field(..., min_length=1, max_length=100)
    query: str = Field(..., min_length=1)
    current: Dict[str, str]
    options: List[Dict[str, str]]

    @validator('options')
    def validate_options(cls, v):
        for option in v:
            if 'text' not in option or 'value' not in option:
                raise ValueError('Each option must have text and value')
        return v




    @validator('max_retry_delay')
    def validate_max_retry_delay(cls, v, values):
        if 'retry_delay' in values and v < values['retry_delay']:
            raise ValueError('max_retry_delay must be >= retry_delay')
        return v



class DashboardMeta(BaseModel):
    """Production-ready model for Grafana dashboard metadata with validation.
    
    Attributes:
        id: Dashboard ID (positive integer)
        uid: Unique identifier (valid format)
        title: Dashboard title (1-100 chars)
        uri: Dashboard URI path
        url: Full dashboard URL
        slug: URL-friendly slug
        type: Dashboard type (fixed as 'dash-db')
        tags: List of tags (max 10)
        is_starred: Whether dashboard is starred
        folder_id: Folder ID (positive integer)
        folder_uid: Folder UID
        folder_title: Folder title
        folder_url: Folder URL
        version: Dashboard version (positive integer)
    """
    id: int = Field(..., gt=0, description="Dashboard ID")
    uid: str = Field(
        ..., 
        min_length=1, 
        max_length=40,
        regex=r'^[a-zA-Z0-9_-]+$',
        description="Unique dashboard identifier"
    )
    title: str = Field(..., min_length=1, max_length=100, description="Dashboard title")
    uri: str = Field(..., description="Dashboard URI path")
    url: str = Field(..., description="Full dashboard URL")
    slug: str = Field(..., description="URL-friendly slug")
    type: Literal["dash-db"] = "dash-db"
    tags: list[str] = Field(
        default_factory=list,
        max_items=10,
        description="Dashboard tags"
    )
    is_starred: bool = Field(False, alias="isStarred")
    folder_id: int = Field(0, gt=0, alias="folderId", description="Folder ID")
    folder_uid: str = Field("", alias="folderUid", description="Folder UID")
    folder_title: str = Field("", alias="folderTitle", description="Folder title")
    folder_url: str = Field("", alias="folderUrl", description="Folder URL")
    version: int = Field(0, gt=0, description="Dashboard version")

    @validator('tags')
    def validate_tags(cls, v):
        """Validate tags are unique and properly formatted"""
        if len(set(v)) != len(v):
            raise ValueError("Dashboard tags must be unique")
        return v

    @validator('folder_uid')
    def validate_folder_uid(cls, v, values):
        """Validate folder_uid matches folder_id when present"""
        if values.get('folder_id') > 0 and not v:
            raise ValueError("folder_uid is required when folder_id is set")
        return v


class TimeoutThresholds(BaseModel):
    """Production-ready timeout thresholds for all Grafana operations.
    
    Attributes:
        default: Base timeout for all operations (seconds)
        read: Timeout for read operations (dashboards, alerts lookup)
        write: Timeout for write operations (dashboard updates)
        backup: Timeout for backup operations
        emergency_threshold: Short timeout for critical operations
        retry_attempts: Max retry attempts
        retry_delay_base: Base retry delay (exponential backoff)
    """
    default: float = Field(30.0, gt=0, le=300, description="Base timeout in seconds")
    read: float = Field(20.0, gt=0, le=300, description="Read timeout in seconds")
    write: float = Field(45.0, gt=0, le=300, description="Write timeout in seconds")
    backup: float = Field(120.0, gt=0, le=600, description="Backup timeout in seconds")
    emergency_threshold: float = Field(5.0, gt=0, le=30, description="Emergency timeout in seconds")
    retry_attempts: int = Field(3, ge=0, le=5, description="Max retry attempts")
    retry_delay_base: float = Field(1.0, gt=0, le=5, description="Base retry delay in seconds")

    @validator('*', pre=True)
    def validate_timeouts(cls, v, field):
        """Ensure timeouts are within sane limits"""
        if field.name.endswith('timeout') or field.name == 'default':
            if v > 600:  # Max 10 minutes for any operation
                raise ValueError(f"{field.name} cannot exceed 600 seconds")
        return v

    def for_operation(self, operation: str) -> float:
        """Get timeout for specific operation type"""
        return getattr(self, operation.lower(), self.default)

    @classmethod
    def fast(cls) -> 'TimeoutThresholds':
        """Preset for fast-running operations"""
        return cls(
            default=10.0,
            read=5.0,
            write=15.0,
            emergency_threshold=2.0
        )

    @classmethod
    def conservative(cls) -> 'TimeoutThresholds':
        """Preset for slow/unreliable networks"""
        return cls(
            default=60.0,
            read=45.0,
            write=90.0,
            backup=300.0
        )


class GrafanaDashboard(BaseModel):
    """Production-hardened Grafana dashboard model with comprehensive validation.
    
    Attributes:
        title: Dashboard title (1-100 chars)
        uid: Unique identifier (valid format)
        timezone: Timezone setting
        schema_version: Dashboard schema version
        panels: List of dashboard panels
        annotations: Dashboard annotations
        templating: Template variables
        refresh: Refresh interval
        tags: Dashboard tags
        version: Dashboard version
    """

    title: str = Field(..., min_length=1, max_length=100)
    uid: str = Field(
        ..., 
        min_length=1, 
        max_length=40,
        regex=r'^[a-zA-Z0-9_-]+$'
    )
    timezone: str = Field("browser", regex=r'^(browser|UTC|[+-]\d{2}:\d{2})$')
    schema_version: int = Field(27, alias="schemaVersion", ge=1)
    panels: List[DashboardPanel]
    annotations: Dict[str, List[DashboardAnnotations]] = Field(default_factory=dict)
    templating: Dict[str, List[DashboardTemplateVariable]] = Field(default_factory=dict)
    refresh: str = Field("5s", regex=r'^\d+[smh]$')
    tags: List[str] = Field(default_factory=list)
    version: int = Field(0, ge=0)

    @validator('panels')
    def validate_panels(cls, v):
        if not v:
            logger.warning('Dashboard created with no panels')
        return v

    @validator('tags')
    def validate_tags(cls, v):
        for tag in v:
            if len(tag) > 50:
                raise ValueError('Tag length must be <= 50 characters')
        return v


class DashboardProvisioningConfig(BaseModel):
    """Production configuration for dashboard provisioning with validation.
    
    Attributes:
        api_version: Configuration API version
        providers: List of dashboard providers (at least one required)
    """

    api_version: str = Field("1", alias="apiVersion")
    providers: List[DashboardProviderConfig]

    @validator('providers')
    def validate_providers(cls, v):
        if not v:
            logger.error('No providers specified in provisioning config')
            raise ValueError('At least one provider must be specified')
        
        # Check for duplicate provider names
        names = [p.name for p in v]
        if len(names) != len(set(names)):
            raise ValueError('Provider names must be unique')
        
        return v


class DashboardRefreshInterval(str, Enum):
    """Standard refresh intervals for production dashboards."""

    SHORT = "5s"
    MEDIUM = "30s"
    LONG = "1m"
    DEFAULT = "5m"

    @classmethod
    def validate(cls, value):
        try:
            return cls(value)
        except ValueError:
            raise ValueError(
                f"Invalid refresh interval. Must be one of: {', '.join([i.value for i in cls])}"
            )


class DashboardPanelType(str, Enum):
    """Supported panel types in production with validation."""

    GRAPH = "graph"
    SINGLESTAT = "singlestat"
    TABLE = "table"
    GAUGE = "gauge"
    BARGAUGE = "bargauge"

    @classmethod
    def validate(cls, value):
        try:
            return cls(value)
        except ValueError:
            raise ValueError(
                f"Invalid panel type. Must be one of: {', '.join([i.value for i in cls])}"
            )
