// k6 load scenario — evidence listing path.
// Used to validate that the evidence query path holds under
// 200 concurrent employees browsing their task history.

import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  stages: [
    { duration: "1m", target: 25 },
    { duration: "3m", target: 100 },
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
      company_code: "load-owner",
      login_id: "load-owner-0",
      password: "P@ssw0rd!",
    }),
    { headers: { "Content-Type": "application/json" } },
  );
  if (login.status !== 200) {
    throw new Error(`setup login failed: ${login.status}`);
  }
  return { session: (login.cookies.sessionid || [])[0]?.value };
}

export default function (data) {
  const params = {
    headers: { Cookie: data.session ? `sessionid=${data.session}` : "" },
  };
  const list = http.get(`${BASE}/api/v1/evidence/tasks?page=1`, params);
  check(list, { "list 200": (r) => r.status === 200 });
  sleep(1);
}
