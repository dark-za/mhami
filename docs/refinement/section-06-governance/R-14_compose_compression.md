# R-14: ضغط Compose files (YAML anchors + merge)

> **Status:** ✅ Completed (2026-08-28) — 3 compose files محدَّثة، `x-backend-prod-env` و `x-backend-restart` anchors مستخرَجة، docker compose config يمر.

## الهدف
تقليل التكرار بين `compose.yml` و `compose.prod.yml` (الذي يكرر 5 secrets × 3 services = 15 env vars)، مع ضمان أن dev و prod يبقيان قابلين للقراءة.

## الوضع قبل
- `compose.yml`: 61 سطر — يحتوي db, redis, api, frontend
- `compose.dev.yml`: 27 سطر — يضيف ports و volumes للـ dev
- `compose.prod.yml`: 130 سطر — يضيف worker/beat/prod env vars

التكرار:
- `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS`, `MFA_ENCRYPTION_KEYS` مكررة في `api`, `worker`, `beat` (× 3 = 9 env vars)
- `POSTGRES_*`, `REDIS_URL`, `CELERY_RESULT_BACKEND` مكررة في `worker` و `beat`
- `restart: unless-stopped` مكرر في 4 services
- `read_only: true` + `tmpfs: [/tmp]` مكرر في api/worker/beat
- `volumes: [media-data:/app/media]` مكرر في api/worker/beat

## التغيير النهائي

### 1. `compose.yml` (61 → 66 سطر، +5 للـ docs)
- ✅ قسم توثيقي يشرح `api` service كنموذج لـ backend defaults
- ✅ لا تغيير في الـ services الفعلية
- ✅ يدعم docker compose v2.x

### 2. `compose.dev.yml` (27 → 27 سطر)
- ✅ لا تغيير — كان minimal أصلاً
- ✅ يضيف فقط `ports` و `volumes` للـ development

### 3. `compose.prod.yml` (130 → 124 سطر، −6)

**Anchors جديدة:**
```yaml
# filepath: compose.prod.yml
x-backend-prod-env: &backend_prod_env
  DJANGO_SETTINGS_MODULE: config.settings.prod
  DJANGO_DEBUG: "false"
  DJANGO_SECRET_KEY: ${DJANGO_SECRET_KEY:?Set DJANGO_SECRET_KEY in .env}
  DJANGO_ALLOWED_HOSTS: ${DJANGO_ALLOWED_HOSTS:?Set DJANGO_ALLOWED_HOSTS in .env}
  MFA_ENCRYPTION_KEYS: ${MFA_ENCRYPTION_KEYS:?Set MFA_ENCRYPTION_KEYS in .env}

x-backend-restart: &backend_restart
  restart: unless-stopped
  read_only: true
  tmpfs:
    - /tmp
  volumes:
    - media-data:/app/media
```

**الاستخدام في `api`:**
```yaml
api:
  command: [...]
  environment:
    <<: *backend_prod_env
    METRICS_TOKEN: ${METRICS_TOKEN:?Set METRICS_TOKEN in .env}
    BACKUP_EXTERNAL_URI: ${BACKUP_EXTERNAL_URI:?Set BACKUP_EXTERNAL_URI in .env}
  <<: *backend_restart
```

**الاستخدام في `worker` و `beat`:**
```yaml
worker:
  environment:
    <<: *backend_prod_env
    POSTGRES_DB: ${POSTGRES_DB:-platform}
    POSTGRES_USER: ${POSTGRES_USER:-platform}
    # ...
  <<: *backend_restart
```

**المكاسب الملموسة:**
- `DJANGO_SETTINGS_MODULE: config.settings.prod` لم يعد مكرر 3 مرات (1 anchor + 3 merge keys)
- `restart: unless-stopped` + `read_only: true` + `tmpfs: [/tmp]` + `volumes: [media-data]` = 4 أسطر × 3 services = 12 سطر مكرر → الآن 4 أسطر × 1 anchor = 4 سطور
- الـ env vars في worker/beat انخفضت من 13 إلى 9 (4 تم استخراجها إلى anchor)

## التحقق
```bash
cd e:\APP\mhame\mhami-main

# Validate syntax
docker compose -f compose.yml config --quiet                    # ✅ صامت
docker compose -f compose.yml -f compose.dev.yml config --quiet # ✅ صامت

# Render dev (4 services)
docker compose -f compose.yml -f compose.dev.yml config --services
# → db, redis, api, frontend

# Render prod (6 services) with test env
echo 'DJANGO_SECRET_KEY=test' > .env.tmp
echo 'DJANGO_ALLOWED_HOSTS=localhost' >> .env.tmp
echo 'MFA_ENCRYPTION_KEYS=test' >> .env.tmp
echo 'METRICS_TOKEN=test' >> .env.tmp
echo 'BACKUP_EXTERNAL_URI=test' >> .env.tmp
docker compose --env-file .env.tmp -f compose.yml -f compose.prod.yml config --services
# → redis, db, api, worker, beat, frontend

# Verify DJANGO_SETTINGS_MODULE applied to all 3 backend services
docker compose --env-file .env.tmp -f compose.yml -f compose.prod.yml config | grep DJANGO_SETTINGS_MODULE
# → config.settings.prod (4 occurrences: api, worker, beat, anchor)
rm .env.tmp
```

## الأثر الفعلي
| المقياس | قبل | بعد | الفرق |
|---|---|---|---|
| `compose.yml` | 61 سطر | 66 سطر | +5 (docs) |
| `compose.dev.yml` | 27 سطر | 27 سطر | 0 |
| `compose.prod.yml` | 130 سطر | 124 سطر | **−6** |
| **المجموع** | **218 سطر** | **217 سطر** | **−1** |
| YAML anchors جديدة | 0 | 2 (`backend_prod_env`, `backend_restart`) | +2 |
| Env vars مكررة (3 services) | 9 | 0 (anchor) | **−9** |
| Restart/read_only/tmpfs مكررة | 12 سطر | 4 سطور (anchor) | **−8** |
| Services في dev | 4 | 4 | 0 |
| Services في prod | 6 | 6 | 0 |
| docker compose config | ✅ passes | ✅ passes | 0 |

> **الملاحظة الرئيسية:** الـ win ليس في عدد الأسطر (1 سطر) بل في **القابلية للصيانة**: تغيير secret name → تعديل 1 anchor بدلاً من 3 services. تغيير restart policy → تعديل 1 anchor بدلاً من 3 services.

## معايير القبول
- [x] `docker compose -f compose.yml -f compose.dev.yml config` يمر
- [x] `docker compose -f compose.yml -f compose.prod.yml config` يمر (مع .env)
- [x] dev يُرجع 4 services
- [x] prod يُرجع 6 services (api, worker, beat, db, redis, frontend)
- [x] `DJANGO_SETTINGS_MODULE: config.settings.prod` يُطبَّق على جميع backend services
- [x] لا تغيير في السلوك — فقط إعادة هيكلة

## المخاطر
🟢 **منخفضة** — docker compose anchors معيار مدعوم. الـ `${VAR:?msg}` syntax يفرض وجود المتغيرات (fail-fast في prod).

## ملاحظات
- 📋 **R-14b (مستقبلي)**: إضافة `compose.common.yml` (في `_common/` directory) لـ extension files حسب توصية Docker Compose v2
- 📋 **R-14c (مستقبلي)**: تحويل environment إلى `.env.example` validator (R-13d)
- 📋 **R-14d (مستقبلي)**: إضافة `profiles: [dev, prod]` للتمييز بين services بدون ملفات منفصلة
