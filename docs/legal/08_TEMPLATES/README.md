# Legal Document Templates

This directory is reserved for shared templates that legal counsel may
use to draft future versions of the documents under `docs/legal/`. It
is not a published artefact and is not subject to the versioning
rules of the per-document directories.

## Suggested template contents

For each `vX.Y.md` document, the template should include:

1. **Status banner** — explicit "placeholder" or "approved" banner
   and review requirements.
2. **Versioning block** — document type, version, effective date,
   supersedes, approver, publisher, next review date.
3. **Product inputs** — the platform behaviour that the document
   must reflect, copied or referenced from the corresponding section
   in the public release plan and approved legal workstream.
4. **Acceptance tracking** — how acceptance is recorded (which
   `LegalDocumentType` and which API endpoint).
5. **Review and change log** — pointer to the per-directory
   `CHANGELOG.md`.
6. **Annexes** — DPIA (`09_DPIA`), breach response
   (`10_BREACH_RESPONSE`), and ROPA (`11_ROPA`) are kept at the
   `docs/legal/` level and referenced, not duplicated, here.
