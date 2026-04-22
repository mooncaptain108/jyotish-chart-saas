## Vedic Jyotish Query
Uses the Vedic Jyotish Chart API - visit this link to see the API (https://github.com/rsaisankalp/vedic-jyotish-api)

Internals 
- Swiss Ephemeris.
- Lahiri VP285
- True Node
- Nutation
- Sidereal Year 365.256

Verified by comparing output against 
- https://www.prokerala.com/astrology/birth-chart
- https://vedicastrochart.com/natal-chart
- JyotishTools application JyotishTools.com
- Verified locations, timezones and daylight saving status at https://www.astro.com/atlas

[Muhurta](static/Muhurta.md)

[About](static/About.md)

compose.yml
```yaml
services:
  jyotish:
    image: mooncaptain/jyotishquery:latest
    environment:
      - MUHURTA_WORKERS=4 #no env var then assigns all.
    ports:
      - "8800:8000"
    container_name: jyotishquery
    restart: unless-stopped
```
