# Offline Garmin export adapter

Internal adapter only.

This document describes a current implementation surface that sits in the repo's bucket model, not a separate canonical layer. The adapter's role fits the `pull` bucket because it reads a local Garmin GDPR export zip and produces derived runtime datasets for later cleaning.

## Current path truth

- The script entrypoint currently lives at `archive/legacy_product_surfaces/garmin/import_export.py`.
- The common runtime output location taught by this adapter doc is `pull/data/garmin/export/`.
- Older docs that taught top-level `data/garmin/export/` are stale for the current bucket-organized repo shape.

## Run

From the repo root:

```bash
python3 archive/legacy_product_surfaces/garmin/import_export.py /path/to/export.zip
```

Optional custom output location:

```bash
python3 archive/legacy_product_surfaces/garmin/import_export.py /path/to/export.zip --output-dir /tmp/garmin-export
```

## Outputs

When using the default bucket-local location, the script writes derived files such as:

- `pull/data/garmin/export/daily_summary_export.csv`
- `pull/data/garmin/export/activities_export.csv`
- `pull/data/garmin/export/hydration_events_export.csv`
- `pull/data/garmin/export/health_status_pivot_export.csv`
- `pull/data/garmin/export/manifest.json`

## Current supported sources

- UDS daily summary export
- sleep daily export
- training readiness export
- acute training load export
- training history export
- health status metric bundle, pivoted by metric type
- summarized activities export
- hydration log export

## Current limitations

- This is an offline adapter only, not a replacement for any live Garmin Connect pull path.
- It is a current implementation surface around legacy Garmin import code, not a claim that Garmin import is a canonical top-level project layer.
- It normalizes a bounded subset and does not promise a broader repo redesign.
- Health status metrics are pivoted only for top-level `value`, `status`, and baseline ranges.
- Activity units are normalized from export-style storage using the current assumptions in that script.
- Some export files mix date strings and epoch timestamps, so unsupported new file variants may need matcher updates.
- Nested FIT backups and richer activity splits or laps remain out of scope for this slice.
