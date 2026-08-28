# Open Decisions

## Status

These items are intentionally unresolved. They must be decided in Phase 00 or before the phase that depends on them. They do not authorize implementation assumptions.

| Decision | Required before | Decision owner | Reason |
| --- | --- | --- | --- |
| Physical server country, operating system, CPU, memory, storage, and network inventory | Phase 02 | Platform Administrator | Determines runtime topology and data-region statement. |
| Backup destination, encryption, frequency, RPO, and restore target | Phase 11 | Platform Administrator | Required for daily-operational recovery claim. |
| Production and staging host separation after resource inventory | Phase 02 | Platform Administrator | Same-host logical isolation is accepted only if inventory supports it. |
| Actual evidence image volume per day | Phase 12 | Pilot owner | Determines storage, worker, and load-test sizing. |
| First tenant provider and connector environment details | Phase 09 | Pilot company owner and technical team | Required to validate connector contract. |
| First company SOPs and verification criteria | Phase 06 and Phase 09 | Pilot Quality Monitor | Required for real templates and AI evaluation. |
| Legal wording for terms, privacy notice, processor terms, and transfer notices | Phase 04 | Legal reviewer and Platform Administrator | Documents are required, but legal text needs review. |
| Exact industry list expansion | Phase 04 | Platform Administrator | Initial list is restaurants/cafes, retail, logistics, and Other. |
