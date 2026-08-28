# FE-03: OpenAPI Types Integration

## Discovery

### Status
- `npm run generate:api` exists
- `src/api/generated-types.ts` must exist
- `frontend/src/api/client.ts` does not use types
- Components use `any` types

### Fix

#### 1. Generate types

```bash
# in development
cd frontend
npm run generate:api
```

This creates `src/api/generated-types.ts` from OpenAPI schema.

#### 2. Type-safe client.ts

**`src/api/client.ts`:**
```typescript
import type { components } from './generated-types';

export type Company = components['schemas']['Company'];
export type User = components['schemas']['UserRead'];
export type TaskInstance = components['schemas']['TaskInstance'];
export type EvidenceItem = components['schemas']['EvidenceItem'];

export async function getCompany(id: string): Promise<Company> {
  return api(`/api/v1/tenancy/companies/${id}/`);
}

export async function listTasks(filters?: {
  branchId?: string;
  status?: string;
}): Promise<TaskInstance[]> {
  const qs = new URLSearchParams();
  if (filters?.branchId) qs.set('branch', filters.branchId);
  if (filters?.status) qs.set('status', filters.status);
  return api(`/api/v1/tasks/?${qs}`);
}

export async function listEvidence(taskId: string): Promise<EvidenceItem[]> {
  return api(`/api/v1/evidence/?task=${taskId}`);
}
```

#### 3. Type-safe components

**`src/pages/tasks/TasksPage.tsx`:**
```typescript
import { listTasks, type TaskInstance } from '../../api/client';

export function TasksPage() {
  const [tasks, setTasks] = useState<TaskInstance[]>([]);
  // No `any`

  useEffect(() => {
    listTasks().then(setTasks);
  }, []);

  return (
    <ul>
      {tasks.map(task => (
        <li key={task.id}>{task.template.name}</li>
      ))}
    </ul>
  );
}
```

#### 4. CI check

In `package.json`:
```json
{
  "scripts": {
    "prebuild": "node scripts/check-generated-types.mjs",
    "predev": "node scripts/check-generated-types.mjs",
    "pretest": "node scripts/check-generated-types.mjs"
  }
}
```

`scripts/check-generated-types.mjs` verifies the file exists and is not stale.

### Acceptance Standards
- AC-1: generated-types.ts exists and is up to date
- AC-2: client.ts uses types
- AC-3: No `any` in the components
- AC-4: typecheck passes
- AC-5: build passes
