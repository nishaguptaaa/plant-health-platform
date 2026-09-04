"""Transparent first-pass estimates of natural light within a zone."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

SOLAR_LUX_PER_W_M2 = Decimal(120)
DEFAULT_TRANSMISSION_FACTOR = Decimal("0.65")
DEFAULT_SKY_VIEW_FACTOR = Decimal("0.50")
DEFAULT_CONTRIBUTION_FACTOR = Decimal("1.00")
TWO_DECIMAL_PLACES = Decimal("0.01")


@dataclass(frozen=True, slots=True)
class LightEstimate:
    """A light estimate and the factors used to calculate it."""

    outdoor_lux: Decimal
    estimated_zone_lux: Decimal
    transmission_factor: Decimal
    sky_view_factor: Decimal
    distance_factor: Decimal
    contribution_factor: Decimal
    method_version: str = "natural_light_heuristic_v1"


def _percentage_factor(
    value: Decimal | None,
    *,
    default: Decimal,
    field_name: str,
) -> Decimal:
    """Convert a percentage from 0–100 into a factor from 0–1."""

    if value is None:
        return default

    if value < 0 or value > 100:
        raise ValueError(f"{field_name} must be between 0 and 100.")

    return value / Decimal(100)


def _distance_factor(distance_m: Decimal | None) -> Decimal:
    """Apply a simple distance penalty for light moving into a room."""

    if distance_m is None:
        return Decimal(1)

    if distance_m < 0:
        raise ValueError("distance_m cannot be negative.")

    return Decimal(1) / ((Decimal(1) + distance_m) ** 2)


def estimate_natural_light_lux(
    *,
    solar_radiation_w_m2: Decimal,
    transmission_percent: Decimal | None = None,
    sky_view_percent: Decimal | None = None,
    distance_m: Decimal | None = None,
    contribution_weight: Decimal | None = None,
) -> LightEstimate:
    """Estimate zone lux from weather and light-source characteristics."""

    if solar_radiation_w_m2 < 0:
        raise ValueError("solar_radiation_w_m2 cannot be negative.")

    if contribution_weight is None:
        contribution_factor = DEFAULT_CONTRIBUTION_FACTOR
    else:
        if contribution_weight < 0 or contribution_weight > 1:
            raise ValueError(
                "contribution_weight must be between 0 and 1."
            )
        contribution_factor = contribution_weight

    transmission_factor = _percentage_factor(
        transmission_percent,
        default=DEFAULT_TRANSMISSION_FACTOR,
        field_name="transmission_percent",
    )
    sky_view_factor = _percentage_factor(
        sky_view_percent,
        default=DEFAULT_SKY_VIEW_FACTOR,
        field_name="sky_view_percent",
    )
    distance_factor = _distance_factor(distance_m)

    outdoor_lux = solar_radiation_w_m2 * SOLAR_LUX_PER_W_M2
    estimated_zone_lux = (
        outdoor_lux
        * transmission_factor
        * sky_view_factor
        * distance_factor
        * contribution_factor
    )

    return LightEstimate(
        outdoor_lux=outdoor_lux.quantize(
            TWO_DECIMAL_PLACES,
            rounding=ROUND_HALF_UP,
        ),
        estimated_zone_lux=estimated_zone_lux.quantize(
            TWO_DECIMAL_PLACES,
            rounding=ROUND_HALF_UP,
        ),
        transmission_factor=transmission_factor,
        sky_view_factor=sky_view_factor,
        distance_factor=distance_factor,
        contribution_factor=contribution_factor,
    )