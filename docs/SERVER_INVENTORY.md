# Server Inventory

## Status

Not started. This document is completed only during Phase 00 through read-only inspection.

## Purpose

Record sanitized facts about the proposed production host before any application or infrastructure change.

## Required Sections

- Host ownership and physical country or region.
- Operating system and kernel.
- CPU, memory, disks, filesystems, and available capacity.
- Docker, Docker Compose, Cloudflare Tunnel, and time-synchronization state.
- Network listeners, firewall posture, and existing service conflicts.
- Existing backup capability and second-destination options.
- Staging separation feasibility.
- Risks, blockers, and decisions required before Phase 02.

## Rules

- Read-only data collection only.
- Do not place credentials, private keys, tokens, or sensitive network details in this file.
- Record date, reviewer, and source command category for each finding.
