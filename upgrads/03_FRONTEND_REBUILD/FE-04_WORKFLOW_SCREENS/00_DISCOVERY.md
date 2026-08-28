# FE-04: P0/P1 screens (Workflow Screens)

## Discovery

### Status
Most pages are placeholders. No real workflow for employees or monitors.

### P0 (Production) - Must complete

1. **Login/Register**
2. **Bootstrap loading**
3. **Role-based navigation**
4. **Locale switching**
5. **Calendar preference**
6. **Error boundaries**
7. **Loading skeletons**

### P1 (workflows) - Must complete

1. **Tasks list & detail** (`/tasks`)
2. **Task execution** (start, submit)
3. **Evidence capture** (`/evidence`)
4. **Review queue** (`/reviews`)
5. **Notifications** list
6. **Profile** view

### P2 (admin) - Deferred

1. People/branch CRUD
2. AI provider config
3. Connector management
4. Exports/Backups UI

## Implementation

### P0: Login Page

**`src/pages/auth/LoginPage.tsx`:**
```typescript
import { useState } from 'react';
import { useNavigate } from 'react-router';
import { useTranslation } from 'react-i18next';
import { api } from '../../api/client';

export default function LoginPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [form, setForm] = useState({ company_code: '', login_id: '', password: '' });
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await api('/api/v1/auth/login', { method: 'POST', body: form });
      navigate('/');
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <input
        name="company_code"
        placeholder={t('auth.company_code')}
        value={form.company_code}
        onChange={e => setForm({ ...form, company_code: e.target.value })}
        required
      />
      <input
        name="login_id"
        placeholder={t('auth.login_id')}
        value={form.login_id}
        onChange={e => setForm({ ...form, login_id: e.target.value })}
        required
      />
      <input
        name="password"
        type="password"
        placeholder={t('auth.password')}
        value={form.password}
        onChange={e => setForm({ ...form, password: e.target.value })}
        required
      />
      {error && <p className="error">{error}</p>}
      <button type="submit" disabled={loading}>
        {loading ? t('common.loading') : t('common.login')}
      </button>
    </form>
  );
}
```

### P1: Tasks Page

**`src/pages/tasks/TasksPage.tsx`:**
```typescript
import { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { listTasks, type TaskInstance } from '../../api/client';

export default function TasksPage() {
  const { t } = useTranslation();
  const [tasks, setTasks] = useState<TaskInstance[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    listTasks()
      .then(setTasks)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingSkeleton />;
  if (error) return <ErrorMessage message={error} />;
  if (tasks.length === 0) return <EmptyState message={t('tasks.empty')} />;

  return (
    <ul className="task-list">
      {tasks.map(task => (
        <li key={task.id} className={`task-item status-${task.status}`}>
          <h3>{task.template.name}</h3>
          <p>{task.template.instructions}</p>
          <span className="status">{task.status}</span>
          {task.due_at && <time>{new Date(task.due_at).toLocaleString()}</time>}
        </li>
      ))}
    </ul>
  );
}
```

### Acceptance Standards
- AC-1: 5 P0 screens implemented
- AC-2: 4 P1 screens implemented
- AC-3: Every screen has loading/empty/error states
- AC-4: accessibility (aria labels, keyboard nav)
- AC-5: bilingual
- AC-6: E2E tests for 5 critical paths
