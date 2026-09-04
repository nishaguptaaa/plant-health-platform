"""SQLAlchemy database models."""

from plant_health.database.models.care import (
    CareEvent,
    CareEventSource,
    CareEventType,
)
from plant_health.database.models.common import TimestampMixin, UUIDPrimaryKeyMixin
from plant_health.database.models.container import (
    Container,
    ContainerMaterial,
    ContainerType,
    PlantContainerHistory,
    PlantContainerRole,
)
from plant_health.database.models.cultivation import (
    GrowingMethodType,
    PlantCultivationHistory,
)
from plant_health.database.models.health import (
    HealthIssue,
    HealthIssueCategory,
    HealthIssueSource,
    HealthIssueStatus,
)
from plant_health.database.models.history import (
    LifecycleEventType,
    LocationChangeReason,
    PlantLifecycleEvent,
    PlantLocationHistory,
)
from plant_health.database.models.identity import (
    Household,
    HouseholdMembership,
    HouseholdRole,
    User,
)
from plant_health.database.models.light import (
    LightSource,
    LightSourceType,
    OrientationSource,
    ZoneLightSource,
)
from plant_health.database.models.observation import (
    ObservationSource,
    ObservationType,
    PlantObservation,
)
from plant_health.database.models.plant import (
    IdentificationStatus,
    Plant,
    PlantStatus,
)
from plant_health.database.models.recommendation import (
    Recommendation,
    RecommendationOutcome,
    RecommendationResult,
    RecommendationSource,
    RecommendationStatus,
    RecommendationType,
)
from plant_health.database.models.site import Site, SiteType, TerrainPosition
from plant_health.database.models.space import Space, SpaceType
from plant_health.database.models.species import Species
from plant_health.database.models.substrate import (
    PlantSubstrateHistory,
    SubstrateCategory,
    SubstrateComponent,
    SubstrateMix,
    SubstrateMixComponent,
)
from plant_health.database.models.task import (
    Task,
    TaskPriority,
    TaskSource,
    TaskStatus,
    TaskType,
)
from plant_health.database.models.treatment import (
    Treatment,
    TreatmentOutcome,
    TreatmentStatus,
)
from plant_health.database.models.weather import (
    WeatherCondition,
    WeatherRecordType,
    WeatherSnapshot,
)
from plant_health.database.models.zone import (
    EnvironmentalZone,
    ObstructionLevel,
    ZoneType,
)

__all__ = [
    "CareEvent",
    "CareEventSource",
    "CareEventType",
    "Container",
    "ContainerMaterial",
    "ContainerType",
    "EnvironmentalZone",
    "GrowingMethodType",
    "HealthIssue",
    "HealthIssueCategory",
    "HealthIssueSource",
    "HealthIssueStatus",
    "Household",
    "HouseholdMembership",
    "HouseholdRole",
    "IdentificationStatus",
    "LifecycleEventType",
    "LightSource",
    "LightSourceType",
    "LocationChangeReason",
    "ObservationSource",
    "ObservationType",
    "ObstructionLevel",
    "OrientationSource",
    "Plant",
    "PlantContainerHistory",
    "PlantContainerRole",
    "PlantCultivationHistory",
    "PlantLifecycleEvent",
    "PlantLocationHistory",
    "PlantObservation",
    "PlantStatus",
    "PlantSubstrateHistory",
    "Recommendation",
    "RecommendationOutcome",
    "RecommendationResult",
    "RecommendationSource",
    "RecommendationStatus",
    "RecommendationType",
    "Site",
    "SiteType",
    "Space",
    "SpaceType",
    "Species",
    "SubstrateCategory",
    "SubstrateComponent",
    "SubstrateMix",
    "SubstrateMixComponent",
    "Task",
    "TaskPriority",
    "TaskSource",
    "TaskStatus",
    "TaskType",
    "TerrainPosition",
    "TimestampMixin",
    "Treatment",
    "TreatmentOutcome",
    "TreatmentStatus",
    "UUIDPrimaryKeyMixin",
    "User",
    "WeatherCondition",
    "WeatherRecordType",
    "WeatherSnapshot",
    "ZoneLightSource",
    "ZoneType",
]