# Section 6: Quality Assurance

## List of Fixes

| # | Title | Priority | Duration |
|---|---|---|---|
| QA-01 | Implement all test layers | P0 | 2 weeks |
| QA-02 | Mandatory coverage threshold | P0 | 3 days |
| QA-03 | Playwright E2E | P0 | 2 weeks (covered in FE-06) |
| QA-04 | Performance tests (k6) | P1 | 1 week |
| QA-05 | Security scanning (OWASP ZAP) | P0 | 1 week |

## QA-01: Test Layers (Detail)

### From TEST_STRATEGY.md
1. Unit tests (domain services + policy) - Required
2. Integration tests (DB constraints, transactions, outbox, jobs) - Required
3. API tests (contracts, errors, auth) - Required
4. Permission tests (tenant, branch, role) - **Missing**
5. Scheduler tests (frozen time) - **Missing**
6. Media tests (signature, size, face) - **Partial**
7. AI tests (fake + contract) - **Partial**
8. Chrome browser tests (Playwright) - **Missing**
9. Security tests - **Partial**
10. Migration tests - **Missing**
11. Backup-restore tests - **Existing**
12. Failure-injection tests - **Missing**
13. Release smoke - **Missing**

### Schedule
| Layer | Current Count | Target Count |
|---|---|---|
| Unit | ~30 | 80+ |
| Integration | ~10 | 30+ |
| API | ~20 | 50+ |
| Permission | 0 | 30+ |
| Scheduler | 0 | 15+ |
| Browser E2E | 0 | 30+ |
| Security | ~5 | 20+ |
| Migration | 0 | 10+ |
| Failure-injection | 0 | 10+ |
| Smoke | 0 | 5+ |
| **Total** | **~65** | **280+** |

## QA-02: Coverage Threshold (Detail)

### Setup
```ini
# pyproject.toml
[tool.coverage.run]
source = ["apps"]
omit = [
    "*/migrations/*",
    "*/tests/*",
    "*/admin.py",
]

[tool.coverage.report]
fail_under = 85
exclude_lines = [
    "pragma: no cover",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if settings.DEBUG:",
    "if TYPE_CHECKING:",
]
```

### CI Integration
```yaml
- name: Run tests with coverage
  run: |
    pytest --cov=apps --cov-report=xml --cov-fail-under=85
- name: Upload to Codecov
  uses: codecov/codecov-action@v4
  with:
    file: ./coverage.xml
```

### Frontend coverage
```json
{
  "coverage": {
    "provider": "v8",
    "reporter": ["text", "html", "lcov"],
    "thresholds": {
      "lines": 70,
      "functions": 70,
      "branches": 65
    }
  }
}
```

## QA-04: Performance Tests (k6) (Detail)

### Scenarios
```javascript
// tests/load/api_load.js
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '2m', target: 50 },   // ramp up
    { duration: '5m', target: 100 },  // sustained
    { duration: '2m', target: 200 },  // peak
    { duration: '2m', target: 0 },    // ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'],  // 95% under 500ms
    http_req_failed: ['rate<0.01'],    // error rate < 1%
  },
};

export default function () {
  const loginRes = http.post(`${__ENV.API_URL}/api/v1/auth/login`, JSON.stringify({
    company_code: 'loadtest',
    login_id: 'loaduser',
    password: 'loadpass',
  }), { headers: { 'Content-Type': 'application/json' } });

  check(loginRes, {
    'login status 200': (r) => r.status === 200,
    'has session': (r) => r.cookies.csrftoken !== undefined,
  });

  sleep(1);
}
```

## QA-05: Security Scanning (Detail)

### OWASP ZAP in CI
```yaml
  zap-scan:
    name: OWASP ZAP Security Scan
    runs-on: ubuntu-latest
    container:
      image: owasp/zap2docker-stable
    steps:
      - uses: actions/checkout@v5
      - name: ZAP Baseline Scan
        run: |
          zap-baseline.py -t http://api:8000 -r zap_report.html -I
      - uses: actions/upload-artifact@v4
        with:
          name: zap-report
          path: zap_report.html
      - name: Fail on high risk
        run: |
          if grep -q "High" zap_report.html; then
            echo "::error::High risk findings"
            exit 1
          fi
```
