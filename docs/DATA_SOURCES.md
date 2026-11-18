# Data-source candidates (not yet ingested)

The links below are **catalogue entries**, not proof that a dataset is suitable for any particular congestion claim. Check licensing and currency per resource before ingesting.

| Source | What it can help with | Caveat |
| --- | --- | --- |
| [Ministry of Transport — traffic counts](https://data.gov.il/he/datasets/ministry_of_transport/sfirot) | Vehicle volumes at sampled locations | Counts **do not measure travel time or congestion** on their own |
| [Ministry of Transport — ad hoc counts](https://data.gov.il/he/datasets/ministry_of_transport/vehicle_counts) | Additional count surveys | Geographic/temporal coverage and methodology vary |
| [Ministry of Transport — road authority GIS](https://data.gov.il/he/datasets/ministry_of_transport/roadauthority) | Finding the relevant road authority | Verify current jurisdiction before assigning responsibility |
| [Ministry of Transport — GTFS](https://gtfs.mot.gov.il/gtfsfiles/) | Planned public transport service | Planned ≠ actual and not a car-speed dataset |
| [Ministry of Transport — SIRI developer page](https://www.gov.il/he/pages/real_time_information_siri) | Public transport real-time data | Access requires the applicable developer process; do not assume open anonymous access |
| [Open Bus / Databus](https://open-bus-map-search.hasadna.org.il/he/about) | Historical/reported public transport performance | Independently verify definitions, update frequency and API/license before use |

## Provenance record required for future real-data imports

`provider`, `canonical_source_url`, `dataset_title`, `release_date`, `accessed_at_utc`, `license`, `collection_method`, `geographical_extent`, `time_extent`, `update_frequency`, `known_gaps`, `transformation_version`, `source_checksum`.

Do not silently upgrade `unverified` to `documented` because a count dataset is present. Validate compatible denominators, location precision, direction and time window. Store only derived aggregate data; avoid personal traces.
