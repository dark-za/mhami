/** Connector enrollment payloads.
 *
 * The OpenAPI schema names this type ``TenantConnectorEnrollment``. The shell
 * re-exports it under the friendlier ``ConnectorEnrollment`` alias and adds
 * the ``shared_secret_fingerprint`` field that the API response includes
 * beyond the schema (the fingerprint is intentionally a non-secret summary
 * surfaced by the backend for UI display).
 */

import type { components } from "../api/generated-types";

type Schema = components["schemas"]["TenantConnectorEnrollment"];

export interface ConnectorEnrollment
  extends Pick<Schema, "id" | "connector_version" | "compatibility_window" | "status" | "health_status" | "last_seen_at" | "revoked_at"> {
  shared_secret_fingerprint: string;
}
