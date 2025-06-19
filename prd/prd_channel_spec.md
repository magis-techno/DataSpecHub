# PRD — Channel Specification Governance

## 1. Purpose
Ensure every data channel has a machine‑readable, versioned specification validated in CI.

## 2. Functional Requirements
1. **Spec Directory**: `channels/<channel>/<spec‑X.Y.Z>.yaml`
2. **Lifecycle Metadata**: `lifecycle.status` (stable/legacy/…)
3. **Sample Data Requirement**: at least 1 sample per release
4. **CI Lint**: schema syntax + sample presence
5. **Alias & Deprecation** handling via `taxonomy/channel_taxonomy.yaml`

## 3. Non‑Functional
* YAML schema lint < 1 s / spec
* Backward compatible changes flagged in PR

## 4. Acceptance
* Creating `radar.v3` auto‑generates docs & passes CI
* Attempting to merge spec without sample → CI fail
