# Delivery roadmap

## Principle

Earn trust before reach: first ship a reproducible case, then publicize findings. A large unverified map is less useful than one actionable, auditable investigation.

| Release | Code deliverable | Acceptance gate |
| --- | --- | --- |
| 0.1.0 — foundation | source-aware traffic screening, validated civic case JSON, RTL static dashboard, demo data | test suite passes; demo labeling explicit; HTML output reproducible |
| 0.2.0 — real data ingestion | first government data adapter + provenance manifest + refresh logic + data quality report | evidence reproducible, licensing/coverage checked; no inferred travel delays from counts |
| 0.3.0 — field investigations | geo coordinates with location privacy checks, OSM map, case submission, reviewer workflow | moderation and correction pathway; no sensitive user traces |
| 0.4.0 — intervention laboratory | baseline vs options, sensitivity analysis, confidence intervals, spillover checklist | uncertainty explicit; no unverified causal conclusion |
| 0.5.0 — accountability | agency contact/response log, public case snapshots, source-linked PDFs | full change log, right of reply and corrections |
| 1.0.0 — extensibility | generic civic domains, contributor onboarding, governance and reusable case schema | auditability, privacy and maintainability verified |

## Operations

- **One first real case, not a nationwide rollout:** choose a road corridor with accessible data, document a legal field measurement plan and publish a dated evidence dossier.
- **Review ownership:** one maintainer checks schema and safety; another reviews external claims and sources where possible.
- **Publish cadence:** after each release, list what is verified, what is hypothesized, what's unresolved and next action.
- **Metrics of impact:** source-backed cases, authority response rate, corrected claims, outcomes independently re-measured — not raw page views or complaint volume.

## Avoid premature complexity

No paid maps, proprietary traffic feeds, citizen GPS tracking, mandatory servers, full-scale ML model or automatic accusations in the initial versions. Introduce infrastructure only when a real ingestion/evaluation need warrants it.
