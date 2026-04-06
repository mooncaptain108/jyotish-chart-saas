## Vedic Jyotish Query
Uses the Vedic Jyotish Chart API - visit this link to see the API (https://github.com/rsaisankalp/vedic-jyotish-api)

The API uses the Swiss Ephemeris.

Verified by comparing output against 
- https://www.prokerala.com/astrology/birth-chart
- https://deva.guru
- https://astrologyayurveda.com/birth-chart-calculator/


Verified locations, timezones and daylight saving status at https://www.astro.com/atlas


#### Designed Pimarily to Search for Auspicious Times
1. For each date, time, location the application shows the Lagna, Navamsa, Rasi data, and the Vimsottari Dashas.
2. The Muhurta search dialog accepts location, start date and time, number of days to search into the future, which rising sign to explore.
3. The baked in screening rules are:
    
    Search only in:

   - Aires (lagna lord Mars)
   - Gemini (lagna lord Sun)
   - Leo (lagna lord Sun)
   - Libra (lagna lord Venus)
   - Sagittarius (lagna lord Jupiter)

    Dismiss if any of the following are afflicted within 5°.

    - MEP of lagna lord house.
    - MEP of occupied house of lagna lord.
    - lagna lord.

    Dismiss if there are any badly placed planets.

    Dismiss if the starting antardasha planet is not a well placed, strong benefic planet.

    Dismiss if there is a concentration of malefic influence.
    Any of the following qualifies as a concentration:
 
    - Any special affliction. Do this search  ("site: https://www.yournetastrologer.com/ special affliction")
    - More than one affliction to the MEP of an MT sign.
    - One affliction to the MEP of an MT sign along with a separate affliction to the MT lord.

    To qualify after the above tests are passed:

    - The Moon (Malefic or Benefic) is in the Nakshatra of a benefic planet.
    - Two or more strong planets. Not counting Rahu or Ketu but could include Mercury and the Moon if either is Malefic. 
    - Five or more strong houses.
    
4. Users may also enter in additional filters:
   - The minimum length of the benefic Antardasha - in days.
   - The minimum strength of any planet. (Note: the minimum strength of the Lagna ruler of the Muhurta is internally set to 60% but can be increased here.)
5. The results are displayed in a list and any result can be displayed in a chart - which includes Lagna, Navamsa, Vimsottari Dashas, Rasi list - with Nakshatras.


        
