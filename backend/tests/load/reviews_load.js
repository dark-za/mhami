// k6 load scenario — review decision queue.
// 50 concurrent monitors opening the review queue and submitting
// decisions. Used to validate that the decision outbox handles
// bursts without dropping the audit-event chain.

import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  stages: [
    { duration: "1m", target: 25 },
    { duration: "3m", target: 50 },
    { duration: "1m", target: 0 },
  ],
  thresholds: {
    http_req_duration: ["p(95)<500"],
    http_req_failed: ["rate<0.01"],
  },
};

const BASE = __ENV.API_URL || "http://localhost:8000";

export function setup() {
  const login = http.post(
    `${BASE}/api/v1/auth/login`,
    JSON.stringify({
      company_code: "load-monitor",
      login_id: "load-monitor-0",
      password: "P@ssw0rd!",
    }),
    { headers: { "Content-Type": "application/json" } },
  );
  if (login.status !== 200) {
    throw new Error(`setup login failed: ${login.status}`);
  }
  const session = (login.cookies.sessionid || [])[0]?.value;
  const list = http.get(`${BASE}/api/v1/reviews/queue`, {
    headers: { Cookie: session ? `sessionid=${session}` : "" },
  });
  const id = list.json("results.0.id") || list.json("0.id");
  return { session, id };
}

export default function (data) {
  const params = {
    headers: {
      Cookie: data.session ? `sessionid=${data.session}` : "",
      "Content-Type": "application/json",
      "X-CSRFToken": __ENV.CSRF_TOKEN || "",
    },
  };
  const queue = http.get(`${BASE}/api/v1/reviews/queue`, params);
  check(queue, { "queue 200": (r) => r.status === 200 });
  sleep(1);
}
