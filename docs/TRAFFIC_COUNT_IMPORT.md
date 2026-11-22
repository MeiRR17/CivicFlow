# Offline traffic-count ingestion (v0.2 development slice)

`python -m src.ingest_counts` converts a **locally supplied, aggregate traffic-count CSV** into an auditable JSON candidate for human review. It does not download from a government website, claim an official source was authenticated, publish a case, or calculate congestion. The current public dashboard continues to display **synthetic** cases and travel-time examples until separately reviewed evidence is integrated.

## 1. Obtain a permitted aggregate dataset

Identify an official/public source, check its terms and usage license, download the file yourself, and retain a copy of the **unchanged original CSV**. Only aggregated vehicle volumes are eligible for this importer. Do not ingest individual vehicle IDs, plate numbers, vehicle-level movements, GPS traces or personal details.

Datasets often have incompatible schemas. This command supports **one row per site, date, time window and direction**. If the source provides one row per day with separate hourly columns, convert those hourly columns to a row-based CSV in a separate documented transformation. Do not silently invent dates, traffic direction, vehicle volumes or time windows.

## 2. Create a source manifest

Compute the real SHA-256 digest of the original CSV. On macOS/Linux:

```bash
shasum -a 256 /path/to/traffic-counts.csv
```

Prepare `local-source-manifest.json` (values below are **illustrative placeholders**, not verified facts or a usable checksum):

```json
{
  "source_kind": "traffic_counts",
  "provider": "EXACT PUBLISHER NAME",
  "canonical_source_url": "https://example.org/source",
  "dataset_title": "EXACT DATASET TITLE",
  "release_date": "2026-11-01",
  "accessed_at_utc": "2026-11-22T10:00:00Z",
  "license": "EXACT LICENSE IDENTIFIER AND TERMS",
  "collection_method": "MEASUREMENT METHOD FROM SOURCE DOCUMENTATION",
  "geographical_extent": "EXACT COVERAGE STATED BY THE SOURCE",
  "time_extent": "REFERENCE PERIOD / OBSERVATION HOURS",
  "coverage_start": "2026-01-01",
  "coverage_end": "2026-10-31",
  "update_frequency": "AS DOCUMENTED BY PUBLISHER",
  "known_gaps": "LIST MISSING PERIODS, SITES, DIRECTIONS OR UNKNOWN ASSUMPTIONS",
  "transformation_version": "raw-source-v1",
  "source_checksum": "REPLACE_WITH_ACTUAL_64_HEX_SHA256",
  "column_map": {
    "site_id": "location_code",
    "date": "observation_date",
    "period": "time_window",
    "direction": "traffic_direction",
    "vehicles": "vehicle_count"
  }
}
```

`column_map` refers to the **actual header names in the source CSV**. All five keys are required and must map to distinct headers. The original source file and signed-off manifest should be kept in a controlled local folder; never commit personal or licensed non-redistributable content to this repository.

The importer checks that every provenance field is nonblank, the canonical URL uses HTTPS, the access timestamp is UTC, the CSV SHA-256 matches, every observation date lies within `coverage_start` and `coverage_end`, and the source follows the documented aggregate row layout. These are mechanical checks, **not** verification that the provider, license or claimed geography are true. Those require a human reviewer.

## 3. Import offline, without publishing

```bash
python -m src.ingest_counts \
  --csv /path/to/traffic-counts.csv \
  --manifest /path/to/local-source-manifest.json \
  --output /path/to/review/traffic-counts-import.json
```

Use `--replace` only when deliberately replacing an existing local output. The destination directory must already exist. The importer writes a temporary file, flushes it and replaces the destination atomically after the full dataset passes validation.

The JSON includes: `schema_version`, `data_kind=aggregate_traffic_counts_only`, `review_status=candidate_unverified`, permitted provenance fields, source-column mapping, an aggregate quality report and normalized count records. Source columns that are not mapped are discarded. Dates are ISO `YYYY-MM-DD`, and daily periods must be `HH:MM-HH:MM`, with the second time later on the same day. Vehicle volumes must be nonnegative ASCII integers. Repeated site/date/period/direction combinations, absent values, malformed time windows, inconsistent source hashes and observations outside declared date coverage **fail the entire import**.

The quality summary reports row count, distinct site and direction counts, first/last observation, zero-volume rows, checks performed and discarded-column policy. The importer has fixed size limits: 25 MiB original CSV, 128 KiB metadata manifest, and 200,000 observation rows. It uses Python's standard library only and requires no cloud access.

## 4. Review and publication gate

This tool **never** calls `src.analyze.rank` or joins volume records with travel-time measurements. Traffic counts alone cannot produce excess-vehicle-minutes, travel-time savings, traffic bottleneck rankings or causal conclusions. Its output is not wired to `src.build_site` and must not be treated as a verified result merely because `review_status` appears in a file.

Before using it to support a real investigation, independently verify publisher identity, original license and redistribution rights, measurement methodology, spatial location/direction, representative days, missingness, time coverage and unit definitions. A distinct, explicit review-and-publish mechanism is a future step. Existing cases must not be upgraded from `unverified` to `documented` just because a count file was imported.

**Development status:** This is an initial importer and validation slice of roadmap v0.2, not a fully integrated official dataset. No actual government dataset has been downloaded, verified or ingested as part of this PR. Tests and validation are deferred to the owner's consolidated review.
