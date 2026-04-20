# Jyotish Query
## Calculation Choices and Code Libraries Used.

Jyotish Query uses the Vedic Jyotish Chart API - visit this link to see the API (https://github.com/rsaisankalp/vedic-jyotish-api)

Internals 
- Swiss Ephemeris.
- Lahiri VP285
- True Node
- Nutation
- Sidereal Year 365.256
- Geo-location is through queries to https://nominatim.org
- Timezone lookup is through a local IANA database
- with cautions for pre 1966 birthdates to use astro.com.

Verified by comparing output against 
- https://www.prokerala.com/astrology/birth-chart
- https://vedicastrochart.com/natal-chart
- JyotishTools application JyotishTools.com
- Verified locations, timezones and daylight saving status at https://www.astro.com/atlas

