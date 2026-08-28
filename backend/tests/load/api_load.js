// k6 load scenario — auth bootstrap and the most-trafficked read paths.
// Mirrors the production traffic mix observed in the pilot evidence
// (login + bootstrap + me).

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
const VUS = parseInt(__ENV.API_VUS || "100", 10);
const PER_ROLE = parseInt(__ENV.API_PER_ROLE || "50", 10);

export default function () {
  const roleIndex = __VU % PER_ROLE;
  const loginRes = http.post(
    `${BASE}/api/v1/auth/login`,
    JSON.stringify({
      company_code: "load-owner",
      login_id: `load-owner-${roleIndex}`,
      password: "P@ssw0rd!",
    }),
    { headers: { "Content-Type": "application/json" } },
  );
  check(loginRes, {
    "login 200": (r) => r.status === 200,
    "has session": (r) => (r.cookies.sessionid || []).length > 0,
  });

  if (loginRes.status === 200) {
    const jar = http.cookieJar();
    const me = http.get(`${BASE}/api/v1/auth/me`, { jar });
    check(me, { "me 200": (r) => r.status === 200 });
    const tasks = http.get(`${BASE}/api/v1/tasks/instances`, { jar });
    check(tasks, { "tasks 200": (r) => r.status === 200 });
  }
  sleep(1);
}
