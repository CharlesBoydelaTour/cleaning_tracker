#!/usr/bin/env bash
set -e
[ -f api/.env.remote ] && set -a && . api/.env.remote && set +a
if [ -d api ]; then
	cd api
	command -v uv >/dev/null 2>&1 || pip install -q uv || true
	[ -d .venv ] && uv sync -q || uv sync -q --frozen || true
	cd - >/dev/null
fi
command -v bun >/dev/null 2>&1 || { curl -fsSL https://bun.sh/install | bash >/dev/null 2>&1 || true; }
[ -d front ] && { export BUN_INSTALL="$HOME/.bun"; export PATH="$BUN_INSTALL/bin:$PATH"; echo 'export BUN_INSTALL="$HOME/.bun"; export PATH="$BUN_INSTALL/bin:$PATH"' >> ~/.bashrc; cd front; bun install --no-progress --ignore-scripts || true; cd - >/dev/null; }
echo SETUP_OK