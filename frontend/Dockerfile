FROM node:24-bookworm-slim AS development

WORKDIR /app/frontend

# Keep the browser toolchain inside the same image used by local E2E checks.
# Debian is an officially supported Playwright base; Alpine's musl runtime is
# not supported by the Chromium build used by the project.
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

COPY package.json ./
COPY package-lock.json ./
# The compose baseline runs the frontend as the unprivileged nginx UID (101).
# Keep the development dependency cache writable by that same UID so Vite can
# rebuild optimized dependencies after a clean self-hosted installation.
RUN npm ci \
    && npx playwright install --with-deps chromium \
    && chown -R 101:101 /app/frontend /ms-playwright

COPY tsconfig.json ./
COPY vite.config.ts ./
COPY index.html ./
COPY src ./src
COPY scripts ./scripts

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

FROM development AS build

RUN npm run build

FROM nginx:1.27-alpine AS production

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/frontend/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
