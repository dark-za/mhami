# PILOT-04: Test Strategy

> **Rule:** Findings must be traceable to an anonymised session record, without exposing participant identity.

## 1. Protocol Review

```bash
Test-Path docs\pilot-evidence\04_USABILITY_PROTOCOL.md
# Expected: True
```

## 2. Evidence Review

```bash
Select-String -Path docs\pilot-evidence\04_USABILITY_FINDINGS.md -Pattern "U-001|P-01|P-05"
# Expected: matches
```

## 3. Privacy Review

```bash
Select-String -Path docs\pilot-evidence\04_USABILITY_FINDINGS.md -Pattern "email|phone|name|address"
# Expected: no direct identifiers
```

## 4. Success Criteria

| Test | Expected |
|---|---|
| Five participant records | passed |
| Three roles represented | passed |
| All tasks measured | passed |
| Findings signed off | passed |
