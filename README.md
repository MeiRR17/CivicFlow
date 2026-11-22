# CivicFlow — מעבדת חקירה אזרחית | Civic Evidence Lab

**Open-source, evidence-first investigations of public systems in Israel.**

CivicFlow aims to turn a public complaint into an evidence-backed, reviewable case: observe → verify → explain → compare interventions → contact the responsible authority → measure outcomes. **The first domain is traffic congestion**, but the case-tracking model is designed to work for public services, accessibility, housing and other civic systems later.

> **Independent initiative. Not affiliated with or speaking for the Israeli Ministry of Transport or any public authority.** The published starter site contains **fictional/synthetic records only**; it makes **no real-world findings** about Israeli roads.

## Live-ready static site (v0.1.0)

A responsive Hebrew RTL public dashboard under [`docs/`](docs/index.html) includes:

- Searchable case register with evidence status, open questions, accountable body, interventions and dated updates.
- Source-aware CSV congestion screening with validation and a clearly limited, illustrative delay proxy.
- Static HTML/CSS/JavaScript generation with **Python standard library only** (no service, tracking or external JS dependencies).
- Reproducible demo datasets and lightweight tests.

**Quick start — Python 3.10+:**

```bash
python -m unittest discover -s tests -v
python -m src.analyze data/example_observations.csv
python -m src.build_site
python -m http.server 8000 --directory docs
```

Open `http://localhost:8000`. Alternatively open [`docs/index.html`](docs/index.html) locally. The build generates `docs/index.html`, `docs/report.json`, and `docs/assets/`. GitHub Pages can publish `main` / `/docs` once enabled by an administrator in repository Settings → Pages; **Pages is not automatically enabled by this commit**.

## The first real case

Use [`docs/investigation-template.md`](docs/investigation-template.md). Record a named road segment and direction, observation period, known data provenance, responsible road authority *if verified*, assumptions, route-wide effects and a before/after test plan. **Only then** move its evidence status from `unverified` to `documented`. Do not label a location as problematic on the basis of traffic counts alone. Real congestion estimates require consistent speed/travel-time and vehicle-volume evidence for the same interval and segment.

To add a case, edit `data/cases.json`, assign a unique ID, and rebuild. Edit `data/example_observations.csv` (or point to a different CSV with `--observations`) for **matched** travel time/volume observation pairs; do not combine unrelated datasets. See [methodology](docs/METHODOLOGY.md) and [source inventory](docs/DATA_SOURCES.md).

## Metric and limitations

For a *single aligned observation window*:

```text
excess_vehicle_minutes = (observed_route_minutes - freeflow_route_minutes) × vehicles_in_window
```

This proxy is for investigating where data collection may be worthwhile. It is **not** a national congestion ranking, number of lost person-hours, a causal assessment or the economic value of a road intervention. Route/direction alignment, sampling design and demand diversion must be checked before making any policy recommendation. Each site's displayed value is the maximum of its entered periods, **not** a sum over different days.

## Offline aggregate traffic-count importer (v0.2 development)

A separate, opt-in **local ingestion CLI** is now available for public-sector traffic-count CSVs, requiring a source manifest with provenance, license, checksum, temporal coverage and explicit source column mapping. It validates the entire source file and writes an atomic JSON dataset marked `candidate_unverified` alongside aggregate quality measures. Nonmapped columns are discarded.

```bash
python -m src.ingest_counts --csv /local/source.csv \
  --manifest /local/source-manifest.json \
  --output /local/review/counts-import.json
```

**Important:** this is an offline adapter, not an official dataset publication. No real dataset is bundled or claimed ingested. Count data are **not** travel-time data and are intentionally excluded from the existing excess-vehicle-minutes dashboard. Human provenance/licensing review and a separate publication gate are still required. See [ingestion requirements and example manifest](docs/TRAFFIC_COUNT_IMPORT.md).

## Roadmap

| Version | Outcome |
| --- | --- |
| **v0.1.0** | Public case register, source validation, synthetic screening and static Hebrew dashboard (implemented) |
| **v0.2.0** | Validated ingestion of an official open dataset with provenance, licenses, timestamps and coverage checks |
| **v0.3.0** | Geographic cases, real map and responsible-authority links; public evidence submission and moderation design |
| **v0.4.0** | Scenario comparison, counterfactuals and before/after evaluation, including network spillovers |
| **v0.5.0** | Public authority response ledger, reproducible case report exports and peer review |
| **v1.0.0** | Multi-domain civic investigation workflows, contributions and stable publishing governance |

See [ROADMAP](docs/ROADMAP.md). Do not treat planned capabilities as already implemented.

## Ground rules

Facts ≠ hypotheses ≠ recommendations. Do not publish personal plates, faces, individual trips, precise personal movements or unverified allegations. Collect no personal location trails. Cite origin, date, license, temporal/spatial coverage and limitations for each real dataset. Give relevant authorities a fair opportunity to respond and preserve their responses accurately. Publish uncertainty and corrections. Prefer safety and accessibility over maximizing vehicle throughput.

For contributions and review rules see [CONTRIBUTING.md](CONTRIBUTING.md). MIT license.
