# FE-01: Clean Router Architecture

## Discovery

### Status
- `main.tsx:14` and `App.tsx:162` both contain `BrowserRouter`
- 14 placeholder pages
- No route guards
- No lazy loading

### Target

```
src/
├── main.tsx              # <BrowserRouter> only
├── App.tsx               # No router
├── routes/
│   ├── index.tsx         # Route table
│   ├── public.tsx        # /login, /register
│   ├── workspace.tsx     # authenticated
│   └── admin.tsx         # role-gated
├── pages/
│   ├── auth/
│   ├── tasks/
│   ├── evidence/
│   ├── reviews/
│   ├── people/
│   ├── admin/
│   └── operations/
├── shell/
│   ├── AppShell.tsx
│   ├── AppErrorBoundary.tsx
│   └── RoleGuard.tsx
└── design-system/
    ├── tokens.ts
    └── i18n.ts
```

### New Code

**`src/routes/index.tsx`:**
```typescript
import { lazy, Suspense } from 'react';
import { Navigate, Route, Routes } from 'react-router';
import { RoleGuard } from '../shell/RoleGuard';

const TasksPage = lazy(() => import('../pages/tasks/TasksPage'));
const EvidencePage = lazy(() => import('../pages/evidence/EvidencePage'));
const PeoplePage = lazy(() => import('../pages/people/PeoplePage'));
const ReviewsPage = lazy(() => import('../pages/reviews/ReviewsPage'));
const AIControlPage = lazy(() => import('../pages/admin/AIControlPage'));
const ExportsPage = lazy(() => import('../pages/operations/ExportsPage'));
const PilotPage = lazy(() => import('../pages/operations/PilotPage'));
const LoginPage = lazy(() => import('../pages/auth/LoginPage'));

export function AppRoutes() {
  return (
    <Suspense fallback={<RouteLoadingScreen />}>
      <Routes>
        {/* Public */}
        <Route path="/login" element={<LoginPage />} />

        {/* Workspace */}
        <Route path="/" element={<RoleGuard roles={['owner', 'monitor', 'employee']}><TasksPage /></RoleGuard>} />
        <Route path="/tasks" element={<RoleGuard roles={['owner', 'monitor', 'employee']}><TasksPage /></RoleGuard>} />
        <Route path="/evidence" element={<RoleGuard roles={['owner', 'monitor', 'employee']}><EvidencePage /></RoleGuard>} />
        <Route path="/people" element={<RoleGuard roles={['owner', 'monitor']}><PeoplePage /></RoleGuard>} />
        <Route path="/reviews" element={<RoleGuard roles={['owner', 'monitor']}><ReviewsPage /></RoleGuard>} />
        <Route path="/admin" element={<RoleGuard roles={['owner']}><AIControlPage /></RoleGuard>} />
        <Route path="/operations" element={<RoleGuard roles={['owner', 'monitor']}><ExportsPage /></RoleGuard>} />
        <Route path="/dashboard" element={<RoleGuard roles={['owner', 'monitor']}><PilotPage /></RoleGuard>} />

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  );
}
```

**`src/App.tsx`:**
```typescript
import { AppShell } from './shell/AppShell';
import { AppRoutes } from './routes';

export function App() {
  return (
    <AppShell>
      <AppRoutes />
    </AppShell>
  );
}
```

**`src/main.tsx` (No Change):**
```typescript
<BrowserRouter>
  <AppErrorBoundary>
    <App />
  </AppErrorBoundary>
</BrowserRouter>
```

### Acceptance Standards
- AC-1: BrowserRouter in main.tsx only
- AC-2: 5+ routes fully implemented
- AC-3: 5+ E2E tests pass
- AC-4: No console warnings
- AC-5: typecheck + build pass
- AC-6: lazy loading works (verified via Network tab)
