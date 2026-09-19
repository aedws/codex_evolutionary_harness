# Source authority

| Truth | Authority |
|---|---|
| Intent | Explicit owner requirement/decision and its source |
| Implementation | Repository code and observed Git/file snapshot |
| Runtime values | Authoritative DB/CSV/resource/API snapshot |
| Verification | TestRun evidence tied to current required code/data/test contract |
| Build identity | Artifact manifest and content digest |
| Deployment | Observed deployed artifact/runtime identity |
| Human acceptance | Explicit decision by the authorized human |
| Status/wiki/checkpoint | Derived projection; never independent verification proof |
| Harness version | Release manifest with evidence-backed capability claims |

Record conflicts instead of silently selecting a convenient source. File presence, source labels and AI confidence do not establish runtime truth. Do not confuse observation time with source modification time.

For tasks explicitly managed by harness.py, its .harness event ledger owns the captured task revisions and test observations; manual documents can reference that lineage but cannot independently override its test result. Existing manual records are not automatically imported or reclassified. Code/data and authorized intent remain their original authoritative sources.
