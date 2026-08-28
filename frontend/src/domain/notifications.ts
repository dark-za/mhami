/** Live notification payloads. */

import type { components } from "../api/generated-types";

export type Notification = components["schemas"]["Notification"];

export type NotificationSeverity = "info" | "success" | "warning" | "danger";

export interface LiveNotification
  extends Pick<Notification, "id" | "title" | "body" | "read_at" | "created_at"> {
  severity: NotificationSeverity;
}
