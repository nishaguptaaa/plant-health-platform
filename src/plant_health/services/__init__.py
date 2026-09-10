"""Application services for the Plant Health Platform."""

from plant_health.services.care import (
    CareRecordingError,
    load_care_history,
    record_care_event,
)
from plant_health.services.household import (
    HouseholdSetupError,
    HouseholdSetupResult,
    create_household_with_owner,
)
from plant_health.services.place_management import (
    PlaceManagementError,
    deactivate_site,
    deactivate_space,
    deactivate_zone,
    rename_household,
    rename_site,
    rename_space,
    rename_zone,
)
from plant_health.services.places import (
    HouseholdPlaces,
    SitePlace,
    SpacePlace,
    ZonePlace,
    load_place_hierarchy,
)
from plant_health.services.plant import (
    PlantSetupError,
    PlantSetupResult,
    create_plant_with_location,
)
from plant_health.services.plant_collection import (
    PlantCollectionItem,
    load_plant_collection,
)
from plant_health.services.plant_management import (
    PlantManagementError,
    PlantManagementResult,
    update_plant_details,
)
from plant_health.services.plant_movement import (
    PlantMovementError,
    PlantMovementResult,
    move_plant,
)
from plant_health.services.site import SiteSetupError, create_site
from plant_health.services.space import SpaceSetupError, create_space
from plant_health.services.task import (
    TaskActionError,
    complete_task,
    create_task,
    skip_task,
    snooze_task,
)
from plant_health.services.zone import (
    ZoneSetupError,
    create_environmental_zone,
)

__all__ = [
    "CareRecordingError",
    "HouseholdPlaces",
    "HouseholdSetupError",
    "HouseholdSetupResult",
    "PlaceManagementError",
    "PlantCollectionItem",
    "PlantManagementError",
    "PlantManagementResult",
    "PlantMovementError",
    "PlantMovementResult",
    "PlantSetupError",
    "PlantSetupResult",
    "SitePlace",
    "SiteSetupError",
    "SpacePlace",
    "SpaceSetupError",
    "TaskActionError",
    "ZonePlace",
    "ZoneSetupError",
    "complete_task",
    "create_environmental_zone",
    "create_household_with_owner",
    "create_plant_with_location",
    "create_site",
    "create_space",
    "create_task",
    "deactivate_site",
    "deactivate_space",
    "deactivate_zone",
    "load_care_history",
    "load_place_hierarchy",
    "load_plant_collection",
    "move_plant",
    "record_care_event",
    "rename_household",
    "rename_site",
    "rename_space",
    "rename_zone",
    "skip_task",
    "snooze_task",
    "update_plant_details",
]
