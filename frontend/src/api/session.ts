export const SESSION_CHANGE_KEY = "mhami.session.changed";
export const SESSION_RECHECK_EVENT = "mhami.session.recheck";

/** Notify other tabs to reread their session from the server, never from storage. */
export function broadcastSessionChange(): void {
  try {
    window.localStorage.setItem(SESSION_CHANGE_KEY, crypto.randomUUID());
  } catch {
    // Storage may be disabled. Tabs also recheck when they regain focus.
  }
}
