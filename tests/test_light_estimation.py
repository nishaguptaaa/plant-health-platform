"""Tests for natural-light estimation."""

from decimal import Decimal

import pytest

from plant_health.light import estimate_natural_light_lux


def test_estimate_natural_light_uses_supplied_factors() -> None:
    """The estimate should expose and apply every input factor."""

    estimate = estimate_natural_light_lux(
        solar_radiation_w_m2=Decimal(170),
        transmission_percent=Decimal(70),
        sky_view_percent=Decimal(60),
        distance_m=Decimal(1),
        contribution_weight=Decimal("0.80"),
    )

    assert estimate.outdoor_lux == Decimal("20400.00")
    assert estimate.estimated_zone_lux == Decimal("1713.60")
    assert estimate.transmission_factor == Decimal("0.7")
    assert estimate.sky_view_factor == Decimal("0.6")
    assert estimate.distance_factor == Decimal("0.25")
    assert estimate.contribution_factor == Decimal("0.80")


def test_estimate_natural_light_uses_documented_defaults() -> None:
    """Missing optional factors should use conservative defaults."""

    estimate = estimate_natural_light_lux(
        solar_radiation_w_m2=Decimal(100),
    )

    assert estimate.outdoor_lux == Decimal("12000.00")
    assert estimate.estimated_zone_lux == Decimal("3900.00")
    assert estimate.transmission_factor == Decimal("0.65")
    assert estimate.sky_view_factor == Decimal("0.50")
    assert estimate.distance_factor == Decimal(1)


def test_estimate_natural_light_rejects_invalid_values() -> None:
    """Impossible percentages and distances should be rejected."""

    with pytest.raises(
        ValueError,
        match="transmission_percent must be between 0 and 100",
    ):
        estimate_natural_light_lux(
            solar_radiation_w_m2=Decimal(100),
            transmission_percent=Decimal(120),
        )

    with pytest.raises(
        ValueError,
        match="distance_m cannot be negative",
    ):
        estimate_natural_light_lux(
            solar_radiation_w_m2=Decimal(100),
            distance_m=Decimal(-1),
        )

    with pytest.raises(
        ValueError,
        match="contribution_weight must be between 0 and 1",
    ):
        estimate_natural_light_lux(
            solar_radiation_w_m2=Decimal(100),
            contribution_weight=Decimal("1.5"),
        )