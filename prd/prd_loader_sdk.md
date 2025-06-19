# PRD — Loader SDK

## 1. Purpose
Provide developers an ergonomic API to iterate dataset files by bundle lock.

## 2. Functional
1. `BundleLoader` loads `*.lock.json`
2. `Channel.files()` yields file paths
3. Configurable `--data-root`
4. Error handling: missing channel data ⇒ exception
5. Future: pluggable IO backend (local, S3, OSS)

## 3. Non‑Functional
* Iterate 1 M files < 60 s (I/O bound)
* No heavy deps (only PyYAML)

## 4. Acceptance
* SDK installed via `pip install dataspec-loader`
* Example script lists at least 1 file per channel
