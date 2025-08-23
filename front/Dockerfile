## Dockerfile front Vite React (dev) - Node + pnpm
FROM node:20-alpine AS base
WORKDIR /app

# Installer pnpm
RUN corepack enable

# Copier manifest
COPY package.json pnpm-lock.yaml* ./

# Installer dépendances (si lock disponible pnpm, sinon via package.json)
RUN if [ -f pnpm-lock.yaml ]; then pnpm install; else pnpm install --no-frozen-lockfile; fi

# Copier le code
COPY . .

EXPOSE 5173
ENV PORT=5173
CMD ["pnpm", "dev", "--host", "0.0.0.0"]
