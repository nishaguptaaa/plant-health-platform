# External Data Sources

This document records the origin, purpose, licensing, privacy behavior, and
commercial-use considerations for external data used by the Plant Health
Platform.

Licensing and provider terms must be reviewed again before any commercial
release.

## Open-Meteo

### Purpose

Open-Meteo supplies site-level weather data used to study relationships among:

- outdoor weather
- cloud cover
- solar radiation
- indoor light
- plant growth
- watering needs
- seasonal health changes

### Data requested

The initial integration requests current values for:

- temperature
- apparent temperature
- relative humidity
- cloud cover
- precipitation
- precipitation probability
- weather condition
- wind speed and direction
- surface pressure
- shortwave solar radiation
- UV index
- daylight status

### Privacy

The application sends:

- latitude
- longitude
- timezone
- optional elevation

The application does not need to send a user's street address. A site may retain
coordinates while its original address is omitted or deleted.

Only the standardized weather snapshot is stored. The initial implementation
does not retain the complete raw API response.

### Access and cost

For personal and other qualifying non-commercial use, Open-Meteo currently
offers a free API that:

- requires no account
- requires no API key
- requires no credit card
- is limited to 10,000 API calls per day
- has no uptime guarantee

The platform should avoid unnecessary calls by respecting each site's weather
synchronization interval.

### License and attribution

Open-Meteo states that its API data is provided under the Creative Commons
Attribution 4.0 license. Attribution is required.

Suggested attribution:

> Weather data by Open-Meteo.com

Official sources:

- [Open-Meteo](https://open-meteo.com/)
- [Forecast API documentation](https://open-meteo.com/en/docs)
- [Pricing](https://open-meteo.com/en/pricing)
- [Terms](https://open-meteo.com/en/terms)

### Commercial-use requirement

The free hosted API is intended for qualifying non-commercial use. Before this
platform charges users, displays advertising, or becomes part of a commercial
product, the weather integration must be reviewed.

Commercial options may include:

- using an Open-Meteo commercial API plan
- self-hosting the open-source Open-Meteo service
- switching to another commercially licensed provider

The provider interface keeps this decision separate from the rest of the
application.

### Verification record

- Last reviewed: September 4, 2026
- Initial provider: Open-Meteo
- Initial endpoint: `https://api.open-meteo.com/v1/forecast`
- Authentication required for personal prototype: No