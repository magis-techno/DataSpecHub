# PRD — Taxonomy & Documentation Portal

## 1. Purpose
Generate human‑friendly docs & diagrams for all specs, categories and versions.

## 2. Functional
1. Script `update_taxonomy_docs.py` → `docs/taxonomy.md`
2. Mermaid ERD in `erd.md`
3. Channel version graph via `semver_graph.py`
4. GitHub Pages deploy (MkDocs)

## 3. Non‑Functional
* Docs build under 2 min in CI
* Zero broken links

## 4. Acceptance
* After any taxonomy change, `docs/taxonomy.md` auto‑updates in PR diff
* GitHub Pages shows updated site within 5 min post‑merge
