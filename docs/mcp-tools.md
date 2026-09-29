# MCP Tools Specification

## Overview
Mhami provides a Model Context Protocol (MCP) server integration allowing external AI agents to perform strictly scoped actions on behalf of authenticated company users.

## Supported MCP Tools

### 1. `system.describe`
- **Description**: Describes the Mhami MCP server status, protocol version, and the active grant context.
- **Required Scope**: `read:reports`
- **Input Schema**:
  ```json
  {
    "type": "object",
    "properties": {},
    "additionalProperties": false
  }
  ```
- **Returns**: `service`, `protocolVersion`, `companyId`, `grantId`, and `scopes`.

### 2. `tasks.list`
- **Description**: Lists task instances filtered within the grant user's role and branch boundaries.
- **Required Scope**: `read:tasks`
- **Input Schema**:
  ```json
  {
    "type": "object",
    "properties": {
      "status": { "type": "string" },
      "limit": { "type": "integer", "minimum": 1, "maximum": 100 },
      "offset": { "type": "integer", "minimum": 0 }
    },
    "additionalProperties": false
  }
  ```
- **Returns**: Paginated list of tasks (`tasks`, `total`, `has_more`, `offset`, `limit`).

### 3. `tasks.transfer.request`
- **Description**: Requests the transfer of a task instance to another active company user in the same branch.
- **Required Scope**: `write:tasks:transfer`
- **Input Schema**:
  ```json
  {
    "type": "object",
    "required": ["task_id", "requested_to_id"],
    "properties": {
      "task_id": { "type": "string" },
      "requested_to_id": { "type": "string" },
      "reason": { "type": "string" }
    },
    "additionalProperties": false
  }
  ```
- **Returns**: The created task transfer record.

## Security Controls
- **Least Privilege**: Actions are strictly bounded by both the grant scopes and the user's active company/branch permissions.
- **Idempotency & Replay Protection**: Each action requires an `idempotency_key` and is signed using HMAC-SHA256 with timestamp and nonce verification.
