# Dataset Manifest

All datasets required by the paper are **DARPA Transparent Computing (TC)
Engagement 3 (E3)** provenance streams. They are released by DARPA into the
**public domain** ("DARPA is releasing these files in the public domain to
stimulate further research"), hosted by Five Directions Inc. on Google Drive.

- Authoritative manifest repo: https://github.com/darpa-i2o/Transparent-Computing
  (clone; `README-E3.md`, `schema/TCCDMDatum.avsc`, `ground truth/`)
- Event data: Google Drive folder referenced by `README-E3.md`
  (`https://drive.google.com/open?id=1QlbUFWAGq3Hpl8wVdzOdIoZLFxkII4EK`)
- Acquisition date: 2026-10-02
- License: public domain (per `README-E3.md`). Raw `.bin`/CSV stays under
  `audit/data/raw/` and is **not** committed to git (size + to be safe).
- Format: Avro-serialized CDM (`TCCDMDatum`), each record wrapped as
  `{"datum": {...}, "CDMVersion": ..., "source": ...}`.

The repository's `data/README.md` calls the four benchmark scenarios
`1r / 3 / 5m / 6r` and the commit's `docs/dataset_statistics.md` lists them under
"theia". The E3 "known good" Theia topics are exactly:
`ta1-theia-e3-official-1r`, `-3`, `-5m`, `-6r`. (Note: the commit's README maps
these to TRACE/CADETS/ClearScope/THEIA, which contradicts the DARPA manifest;
they are all Theia E3 streams. This audit uses the Theia E3 naming.)

---

## 1. theia-3  (`ta1-theia-e3-official-3`)

| Field | Value |
|---|---|
| Source URL | Google Drive file id `10KZG-8ET9CRG9qc8OmEQMaCgf6uSEylD` |
| Archive | `ta1-theia-e3-official-3.bin.tar.gz` (27,574,561 bytes) |
| Extracted | `ta1-theia-e3-official-3.bin` (247,253,759 bytes) |
| Download date | 2026-10-02 |
| License | Public domain (DARPA / Five Directions) |
| Status | **OBTAINED & PARSED** |
| Parsed | 20,157 nodes / 297,777 edges / 0 skipped |
| Validation | `audit/parsing/theia3_validation.md` |

## 2. theia-5m  (`ta1-theia-e3-official-5m`)

| Field | Value |
|---|---|
| Source URL | Google Drive file id `1krhA9Rco7W5hZG6md3TqB1aH2FOjxBn3` |
| Archive | `ta1-theia-e3-official-5m.bin.tar.gz` (20,501,876 bytes) |
| Extracted | `ta1-theia-e3-official-5m.bin` (153,067,226 bytes) |
| Download date | 2026-10-02 |
| License | Public domain |
| Status | **OBTAINED & PARSED** |
| Parsed | 34,835 nodes / 464,858 edges / 0 skipped |
| Validation | `audit/parsing/theia5m_validation.md` |

## 3. theia-1r  (`ta1-theia-e3-official-1r`)

| Field | Value |
|---|---|
| Source URL | Google Drive file id `1yksk4I9DBnl0Tca_Y0eaiNcpRNccB9sF` |
| Archive | `ta1-theia-e3-official-1r.bin.tar.gz` (~estim. 500 MB) |
| Download date | attempted 2026-10-02 |
| License | Public domain |
| Status | **NOT OBTAINED — Google Drive quota** |
| Reason | Google Drive returned HTTP 403 "Too many users have viewed or downloaded this file recently" for anonymous download, persistently across repeated attempts (background retry loop, 20 attempts over >40 min). |
| Expected (paper `docs/dataset_statistics.md`) | 408,320 nodes / 9,295,127 edges |
| Alternative access | Authenticated Google account, or the E5 release (folder `1okt4AYElyBohW4XiOBqmsvjwXsnUjLVf`), or HDFS mirror. Parser already supports it: drop the `.bin` in `audit/data/raw/theia/` and run `audit/scripts/parse_real.py`. |

## 4. theia-6r  (`ta1-theia-e3-official-6r`)

| Field | Value |
|---|---|
| Source URL | Google Drive file id `13rgPgHunDV1dSNX9U8bSOem56StlUmqF` |
| Archive | `ta1-theia-e3-official-6r.bin.tar.gz` (~estim. 1 GB) |
| Download date | attempted 2026-10-02 |
| License | Public domain |
| Status | **NOT OBTAINED — Google Drive quota** |
| Reason | Same persistent HTTP 403 quota error as 1r. |
| Expected (paper) | 1,123,475 nodes / 18,206,475 edges |
| Alternative access | Authenticated account / E5 release / HDFS mirror. |

## 5. Ground truth & schema (obtained)

| File | Source file id | Status | Use |
|---|---|---|---|
| `TC_Ground_Truth_Report_E3_Update.pdf` | `1mrs4LWkGk-3zA7t7v8zrhm0yEDHe57QU` | OBTAINED | ACT/TA5.1 attack narrative; maps malicious actions to time windows/hosts |
| `operational_event_log.md` | `1mnx73nb0KMX4EbgSiBLu0tkKrQ34P96H` | OBTAINED | E3 test-range activity log |
| `TCCDMDatum.avsc` | `1oGMbSIZ73lh0xs8PUg--3Bj_wtC1q85-` | OBTAINED | CDM Avro schema |
| `ta3-java-consumer.tar.gz` | `1Yg_487Ynr9gV3oRy3KmS2tOj8RNomVY6` | available | reference parser |

## 6. TRACE / CADETS / ClearScope

The paper's cross-dataset table names TRACE, CADETS, ClearScope and THEIA, but
the four committed benchmark rows use the Theia E3 files `1r/3/5m/6r` (see
`docs/dataset_statistics.md`, which titles them "Theia E3"). No distinct TRACE,
CADETS or ClearScope parsed CSVs exist anywhere in the repo, and no script
references them. Therefore:

- **TRACE / CADETS / ClearScope as separate datasets: NOT USED by the
  repository and NOT REQUIRED to reproduce its tables.** The E3 releases of
  those performers exist on the same Google Drive folder
  (`data/cadets/`, `data/clearscope/`, `data/trace/`) and are public domain, but
  the repo has no parser path exercised for them and the committed numbers do
  not depend on them. They are noted here as a possible genuine cross-dataset
  extension (see `audit/reports/`).

  Note: CADETS, ClearScope and TRACE E3 streams are recorded in the **Legacy
  (pre-CDM) format**, not the CDM Avro format. The repo's parser
  (`cdm_parser.py`) only handles CDM. Using them would require an additional
  parser. This is documented, not worked around.

## 7. Summary

| Dataset | Required? | Obtained? | Parsed? | Notes |
|---|---|---|---|---|
| theia-3 | yes | yes | yes | 297,777 edges, exact match to paper |
| theia-5m | yes | yes | yes | 464,858 edges, exact match to paper |
| theia-1r | yes | **no** | no | Drive quota 403 |
| theia-6r | yes | **no** | no | Drive quota 403 |
| TRACE/CADETS/ClearScope | no (not used) | no | no | legacy format; out of scope |
| E3 ground-truth PDF | yes | yes | n/a | for real-label separation |
