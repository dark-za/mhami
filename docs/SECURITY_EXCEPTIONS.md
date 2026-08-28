# Security Exceptions

This document records every accepted deviation from a security
control. Every entry must be:

1. Approved by the Security Lead.
2. Time-boxed (review date in the calendar).
3. Replaced by a permanent fix as soon as possible.

> **No exception without a review date.** The CI gate refuses to
> merge a flagged ZAP alert unless the alert ID is listed here with
> an unexpired review date.

## Format

```
## <alert-id>: <short title>

- **Approved by:** <name>
- **Approved on:** YYYY-MM-DD
- **Review by:** YYYY-MM-DD
- **Scope:** <URL pattern, file, or component>
- **Reason:** <business or technical rationale>
- **Mitigation:** <compensating control>
- **Exit plan:** <how the exception is removed>
```

## Active exceptions

_None — every ZAP alert is either fixed or in flight._
