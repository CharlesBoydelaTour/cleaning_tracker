# Dockerfile front Vite React (dev)
FROM oven/bun:1 as base
WORKDIR /app

# Copier manifests
COPY package.json bun.lockb ./

# Installer deps (cache layer)
RUN bun install

# Copier code
COPY . .

EXPOSE 5173
CMD ["bun", "run", "dev", "--host", "0.0.0.0"]
