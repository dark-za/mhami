# Pilot Profile

## Status

Exit dossier issued by `PILOT-ASSURANCE-02`. The pilot company, branches, owner, monitors, employees, Chrome devices, shifts, task templates, and success measures are provisioned in the `pilot` app (`PilotProgram`, `PilotWeeklyReport`, `PilotIssue`, `PilotChangeRequest`). See `docs/PHASE12_EXIT_DOSSIER.md` and the Phase 12 reports in `docs/`.

## Purpose

Describe the internal pilot organization used to validate the platform.

## Required Facts

- **Company sector and owner.** A single internal operating company in the food-service / quick-service-restaurant sector, owned and operated by the platform owner. It is modeled as one `Company` with a one-to-one `PilotProgram` record. The pilot owner is the internal operations lead accountable for the pilot outcome.

- **Branches.** Three pilot branches (program target `branch_count_target=3`; the model allows scaling up to five per Phase 12), each in a distinct operating timezone with its own operational-day cutoff (e.g., 23:59 local) used for shift and task rollover. Branches are isolated tenants for the pilot.

- **Employees.** Approximately thirty employee accounts (`employee_count_target=30`) across the three branches: shift workers, shift leads, and branch monitors. A subset are cross-trained as Quality Monitors who perform review decisions.

- **Monitors and Chrome devices.** Each branch has at least one designated Quality Monitor. All task submission is Chrome-only (`chrome_device_count` captures the enrolled ChromeOS / Chrome device fleet per station; the pilot enforces the browser-only policy with no gallery-upload fallback). Devices are managed and enrolled before go-live.

- **Weekly shift patterns and transfers.** Simple weekly shift patterns (opening, mid, closing) per branch with overlapping handover windows. Transfer scenarios cover shift-lead handover of open tasks and monitor reassignment of flagged evidence.

- **Expected volume.** Expected task volume of roughly 30–60 task instances per branch per day (checklists, inspections, handovers). Expected image volume of roughly 150–400 evidence images per branch per day at peak (opening prep, mid-day inspection, close). Peak use periods are opening prep, lunch service, and close-of-day.

- **AI provider, connector owner, test environment.** `ai_provider_name` is a private vision model endpoint exposed through the Tenant Connector (shadow mode only). `connector_owner` is the internal platform SRE / connector team accountable for connector enrollment and health. `test_environment` is a staging-equivalent pilot deployment (`pilot`) isolated from production data.

- **Success measures and escalation contacts.** `success_measures`, `escalation_contacts`, `operating_checklist`, and `weekly_metrics_goal` are captured as JSON on the `PilotProgram` and refined weekly via `PilotWeeklyReport`. Escalation contacts include the pilot owner, connector owner, and platform on-call.
