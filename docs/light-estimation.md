# Light Estimation Method

## Purpose

The first light estimator provides a transparent starting point for comparing
plant-placement zones.

It is not intended to replace a lux meter, a calibrated sensor, or a detailed
three-dimensional lighting simulation.

## Inputs

The estimate can use:

- outdoor shortwave solar radiation from the weather provider
- window or skylight transmission percentage
- estimated visible-sky percentage
- distance from the light source
- the source's estimated contribution to the zone

## Version 1 formula

Outdoor illuminance is approximated as:

    outdoor_lux = solar_radiation_w_m2 × 120

Estimated zone illuminance is:

    estimated_zone_lux =
        outdoor_lux
        × transmission_factor
        × sky_view_factor
        × distance_factor
        × contribution_factor

The distance factor is:

    distance_factor = 1 / (1 + distance_m)²

## Default assumptions

When information is missing, Version 1 uses:

    window transmission = 65%
    visible sky = 50%
    distance = 0 meters
    source contribution = 100%

These defaults are intentionally visible in the returned result.

## Multiple windows and light sources

Each environmental zone may be linked to multiple light sources through
`ZoneLightSource`.

The future zone-level estimator can calculate each source's estimated
contribution separately and combine them.

Examples include:

- two windows on different walls
- a window plus a skylight
- natural light plus a grow light
- several grow lights over one shelf

## Manual measurements

Manual lux measurements are stored in `EnvironmentalMeasurement`.

A measurement can identify:

- the environmental zone
- the individual plant
- the contributing light source
- whether it was taken at leaf level
- the measuring device
- the time and duration
- the recorded lux, temperature, and humidity
- confidence and notes

Measurements at plant-leaf level are more useful than measurements taken in an
unrelated part of the room.

## Limitations

The Version 1 calculation does not fully model:

- sun angle
- window direction
- time of year
- room geometry
- reflections from walls
- trees and buildings
- curtains and blinds
- spectral differences
- exact grow-light beam patterns
- changing shadows
- the nonlinear behavior of phone light sensors

The distance calculation is a ranking heuristic. A window is an extended light
source, so it does not behave exactly like a point source following a perfect
inverse-square law.

## Calibration plan

Actual lux measurements will gradually replace generic assumptions.

A later estimator can compare:

    measured indoor lux ÷ outdoor estimated lux

for each zone, time, and weather condition.

That observed ratio can become a zone-specific calibration factor. Repeated
measurements will let the platform learn how a real room behaves without
requiring users to upload or measure a complete floor plan.

## Interpretation

Use Version 1 estimates to:

- compare likely brighter and darker zones
- prioritize where to take real measurements
- identify major seasonal changes
- create cautious placement suggestions

Do not use Version 1 estimates as proof that a plant receives an exact amount
of light.