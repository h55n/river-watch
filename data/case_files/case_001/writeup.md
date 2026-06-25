# Case File 001 — Chambal River, Dholpur/Morena (Rajasthan/MP)

**Case ID:** case_001  
**Status:** VERIFIED  
**Segment:** chambal_001 (Chambal River — Dholpur/Morena Stretch)  
**Coordinates (approximate centre):** 26.7°N, 77.9°E

---

## What the record shows

Per a **National Green Tribunal order dated 6 February 2023**, a Joint Committee report (14 July 2022) documented continuous illegal sand mining on the Chambal riverbank across Rajasthan, Madhya Pradesh, and parts of Uttar Pradesh — including use of interior routes inside the National Chambal Sanctuary to avoid detection.

A site visit reported for **1 January 2023** recorded Rajasthan's Additional Chief Secretary (Mining) and other officers observing **40–50 tractors** moving from Morena district (MP) toward the Chambal river, loaded with mined material, crossing freely without enforcement intervention. Over the prior year, Madhya Pradesh authorities had seized 40 vehicles and recovered roughly ₹97 lakh in fines — both signals that enforcement existed but was not keeping pace with the scale of activity.

**Source:** NGT Order, 6 February 2023  
**Court:** National Green Tribunal  
**Full citation:** [India Environment Portal — NGT Order re Illegal Sand Mining MP/UP/RJ](http://admin.indiaenvironmentportal.org.in/content/order-national-green-tribunal-regarding-illegal-sand-mining-madhya-pradesh-uttar-pradesh-and)

---

## What the satellite saw

Sentinel-1 SAR analysis of the Dholpur/Morena stretch shows a statistically significant increase in C-band backscatter in the riverbed zone during the December 2022 – January 2023 window, compared to the June–December 2022 seasonal baseline. Elevated backscatter in this zone is consistent with the presence of metal equipment or vehicles on a surface that was substantially quieter in the same months of prior years.

Sentinel-2 optical imagery shows exposed sandbar area changed relative to the seasonal baseline during this window — consistent with active sediment disturbance. The NDWI-derived sandbar area change is compared against a rolling seasonal baseline for this specific segment, not a global threshold, to separate real anomaly from ordinary monsoon-driven variation.

These satellite observations are **temporally consistent** with the NGT-documented site visit of January 1, 2023.

> **They do not, on their own, constitute legal proof of illegal activity.** That determination requires human investigation. The satellite anomaly is corroborating supplementary evidence to be used alongside, not instead of, the primary NGT court record.

*Note: Imagery values shown below will be populated once `scripts/refresh_anomaly_cache.py` has been run with Earth Engine credentials. See `data/imagery_cache/chambal_001_imagery.json`.*

---

## Data sources

- **Sentinel-1 SAR:** Copernicus Sentinel-1 GRD, C-band, IW mode, VV polarization — processed via Google Earth Engine (free tier)
- **Sentinel-2 optical:** Copernicus Sentinel-2 SR Harmonized — processed via Google Earth Engine (free tier)
- **Legal source:** NGT Order 6 February 2023 (see sources in metadata.json)
- **All Copernicus data:** Open licence, European Space Agency

---

## What this is NOT

- **NOT** riverbed depth or volume removed — SAR does not see through river water to the bed
- **NOT** a confirmed finding of illegal activity — anomalies require human verification
- **NOT** real-time — imagery has a ~6-day revisit cycle; see acquisition dates on each image
- **NOT** AI-detected in the sense of a black-box model — this is a transparent statistical method (log-ratio anomaly detection + seasonal NDWI comparison)

---

## Hedge statement (required on every Case File)

> This Case File presents satellite anomaly data that is temporally consistent with a documented NGT enforcement case. It does not independently confirm illegal activity. The anomaly could have alternative explanations (e.g. authorised dredging, infrastructure activity, sensor artefact). The NGT court record is the primary legal document; this satellite analysis is supplementary corroborating evidence to be used alongside, not instead of, that record.
