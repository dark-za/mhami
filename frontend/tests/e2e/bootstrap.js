// filepath: frontend/tests/e2e/bootstrap.js
/**
 * Shared browser/UI integration test helpers.
 *
 * Mocks all required API endpoints so the SPA can boot and run tests
 * deterministically without a real Django backend. Each test is expected
 * to call {@link installNetworkStubs} in `beforeEach`.
 *
 * GET contracts are mocked with accurate shapes matching the frontend's
 * `api()` expectations ({memberships, instances, transfers, notifications,
 * branches, roles, etc.}) to avoid leaking to a live backend.
 */
export async function installNetworkStubs(page) {
  // Fail-closed catch-all BEFORE specific stubs: unhandled /api/v1/** requests
  // abort (blockedbyclient) and make tests fail instead of silently returning 200.
  // Use /api/v1/** to avoid blocking Vite source imports like src/api/client.ts.
  await page.route("**/api/v1/**", async (route) => {
    const url = route.request().url();
    const allowList = [
      "/api/v1/bootstrap",
      "/api/v1/notifications",
      "/api/v1/tasks/instances",
      "/api/v1/tasks/transfers",
      "/api/v1/tasks/requests",
      "/api/v1/tasks/transfer-recipients",
      "/api/v1/auth/company/members",
      "/api/v1/organizations/branches",
      "/api/v1/organizations/job-roles",
      "/api/v1/reviews/dashboard",
      "/api/v1/reviews/queue",
      "/api/v1/reviews/policy",
      "/api/v1/ai/criteria",
      "/api/v1/ai/shadow",
      "/api/v1/ai/provider",
      "/api/v1/connectors/enrollment",
      "/api/v1/agent/grants",
      "/api/v1/agent/scopes",
      "/api/v1/agent/logs",
      "/api/v1/exports/policy",
      "/api/v1/exports/requests",
      "/api/v1/auth/login",
      "/api/v1/auth/logout",
      "/api/v1/setup/initialize",
      "/api/v1/evidence/tasks",
    ];
    const shouldFallback = allowList.some((p) => url.includes(p));
    if (shouldFallback) {
      await route.fallback();
    } else {
      await route.abort("blockedbyclient");
    }
  });

  await page.route("**/api/v1/auth/login", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        session: "stub-session-token",
        user: { id: "user-1", role: "owner" },
      }),
    });
  });

  await page.route("**/api/v1/bootstrap", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        installation: { setup_required: false },
        company: { id: "acme", name: "Acme", locale: "en" },
        current_user: { id: "user-1", role: "owner", is_authenticated: true },
        permissions: ["admin"],
        branches: [],
        branch_scope: [],
        enabled_modules: ["dashboard", "operations", "tasks", "evidence", "people", "reviews", "admin", "agent_access"],
      }),
    });
  });

  await page.route("**/api/v1/notifications**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ notifications: [] }),
    });
  });

  await page.route("**/api/v1/tasks/instances**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ instances: [] }),
    });
  });

  await page.route("**/api/v1/tasks/transfers**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ transfers: [] }),
    });
  });

  await page.route("**/api/v1/tasks/requests**", async (route) => {
    // Handles /api/v1/tasks/requests and /api/v1/tasks/requests/list variants
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ requests: [] }),
    });
  });

  await page.route("**/api/v1/tasks/transfer-recipients**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ recipients: [] }),
    });
  });

  await page.route("**/api/v1/auth/company/members**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ memberships: [] }),
    });
  });

  await page.route("**/api/v1/organizations/branches**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ branches: [] }),
    });
  });

  await page.route("**/api/v1/organizations/job-roles**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ roles: [] }),
    });
  });

  await page.route("**/api/v1/reviews/dashboard**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        company: { id: "acme", name: "Acme", code: "acme", status: "active" },
        summary: {
          completed_today: 7,
          overdue: 0,
          quality_exceptions: 0,
          open_issues: 0,
          pending_review: 0,
          employees: 3,
          monitors: 1,
          branches: 2,
          completed_in_period: 7,
          pending: 2,
          in_progress: 1,
          cancelled: 0,
        },
        branches: [],
        period: "day",
        trend: [{ date: "2026-09-01", completed: 7, created: 0 }],
      }),
    });
  });

  await page.route("**/api/v1/reviews/queue**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ items: [] }),
    });
  });

  await page.route("**/api/v1/reviews/policy**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        id: "policy-1",
        employee_score_visibility: "summary",
        historical_report_restatement: false,
        monitor_approval_required: true,
        sensitive_task_claim_restricted: true,
        extra_evidence_required: false,
        owner_alerts_enabled: true,
        approved_task_weight_cap: 5,
      }),
    });
  });

  await page.route("**/api/v1/ai/criteria**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ criteria: [] }),
    });
  });

  await page.route("**/api/v1/ai/shadow**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        company: { id: "acme", name: "Acme", code: "acme" },
        summary: { total_runs: 0, completed: 0, needs_review: 0, agreement_rate: 0 },
        runs: [],
      }),
    });
  });

  await page.route("**/api/v1/ai/provider**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        id: "provider-1",
        company: "acme",
        provider_name: "fake",
        endpoint_url: "",
        model_name: "",
        credential_reference: "",
        monthly_token_limit: 10000,
        monthly_cost_limit: "0.00",
        enabled: true,
      }),
    });
  });

  await page.route("**/api/v1/connectors/enrollment**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ enrollment: null }),
    });
  });

  await page.route("**/api/v1/agent/grants**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ grants: [] }),
    });
  });

  await page.route("**/api/v1/agent/scopes**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ scopes: [] }),
    });
  });

  await page.route("**/api/v1/agent/logs**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ logs: [] }),
    });
  });

  await page.route("**/api/v1/exports/policy**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        id: "policy-1",
        future_notification_boundaries: ["emails"],
        external_storage_boundaries: ["none"],
        provider_review_checklist: ["support approval"],
      }),
    });
  });

  await page.route("**/api/v1/exports/requests**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ requests: [], exports: [] }),
    });
  });

  await page.route("**/api/v1/evidence/tasks/**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ evidence: [], issues: [], messages: [] }),
    });
  });
}

export async function installUnauthenticatedNetworkStubs(page) {
  await page.route("**/api/v1/**", async (route) => {
    const url = route.request().url();
    const allowList = ["/api/v1/bootstrap", "/api/v1/notifications", "/api/v1/auth/login", "/api/v1/setup/initialize"];
    if (allowList.some((p) => url.includes(p))) {
      await route.fallback();
    } else {
      await route.abort("blockedbyclient");
    }
  });

  await page.route("**/api/v1/bootstrap", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        installation: { setup_required: false },
        current_user: { is_authenticated: false },
        company: null,
        permissions: [],
        branches: [],
        branch_scope: [],
        enabled_modules: [],
      }),
    });
  });

  await page.route("**/api/v1/notifications/**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ notifications: [] }),
    });
  });
}
