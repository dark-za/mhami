# C-01: Verification Commands

> **Instructions:** Run these commands before and after the modification, and record the results in `04_RESULTS.md`.

## Phase 1: Pre-Fix Proof

### Command 1.1: Confirm presence of nested Router

```bash
# PowerShell
Select-String -Path "frontend\src\main.tsx" -Pattern "BrowserRouter"
Select-String -Path "frontend\src\App.tsx" -Pattern "BrowserRouter"
```

**Expected output (before fix):**
```
main.tsx:14:      <BrowserRouter>
App.tsx:162:    <BrowserRouter>
App.tsx:164:    </BrowserRouter>
```

**Meaning:** `BrowserRouter` exists in two files.

### Command 1.2: Run the application and observe the warnings

```bash
cd frontend
npm run dev
# Open http://localhost:5173
# Open DevTools Console
```

**Expected output:**
```
Warning: You cannot nest <BrowserRouter> inside another <BrowserRouter>.
```

**Meaning:** React Router warns.

### Command 1.3: Test the navigation

```bash
# in DevTools
window.history.pushState({}, '', '/evidence')
window.location.reload
# Note: the page does not change or shows 404
```

### Command 1.4: Count BrowserRouter instances

```bash
grep -c "BrowserRouter" frontend/src/*.tsx
```

**Expected output:** `2` (in main.tsx and App.tsx)

### Command 1.5: Count Routes

```bash
grep -c "<Routes>" frontend/src/*.tsx
```

**Expected output:** `1` (in App.tsx inside AppShellHost)

---

## Phase 2: Post-Fix Verification

### Command 2.1: Confirm only one BrowserRouter exists

```bash
grep -c "BrowserRouter" frontend/src/*.tsx
```

**Expected output:** `1` (in main.tsx only)

### Command 2.2: Verify Routes are moved to App

```bash
grep -c "<Routes>" frontend/src/App.tsx
```

**Expected output:** `1`

### Command 2.3: typecheck

```bash
cd frontend
npm run typecheck
```

**Expected output:** `> tsc -p tsconfig.json --noEmit` without errors, exit code 0.

### Command 2.4: build

```bash
npm run build
```

**Expected output:** `vite build` passes, exit code 0.

### Command 2.5: Run dev and verify navigation

```bash
npm run dev
# Open http://localhost:5173
# navigate between /tasks and /evidence
# Note: no warnings, smooth navigation
```

### Command 2.6: E2E test

```bash
# after adding playwright test
npx playwright test
```

**Expected output:** all tests pass, exit code 0.

---

## Phase 3: Regression Tests

### Command 3.1: Run all tests

```bash
cd frontend
npm run test
```

**Expected output:** all tests succeed.

### Command 3.2: Verify locale state

```bash
# in DevTools
localStorage.getItem('locale')
# must be 'ar' or 'en' based on last selection
```

### Command 3.3: Verify Calendar preference

```bash
localStorage.getItem('calendar')
# must be 'gregorian' or 'hijri'
```

---

## 4. Final Acceptance

- ✅ Command 1.1 shows two files before, one file after
- ✅ Command 1.2 does not show warning after
- ✅ Command 2.3 passes
- ✅ Command 2.4 passes
- ✅ Command 2.6 passes

If any of these fail → **Rejection**, Re-implement.
