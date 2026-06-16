#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

MODE="${1:-docker}"

usage() {
  cat <<'EOF'
Usage:
  bash dev.sh         Prepare missing prerequisites and start the Docker dev stack
  bash dev.sh docker  Same as default
  bash dev.sh local   Prepare local Python dev environment and run migrations
  bash dev.sh help    Show this help
EOF
}

command_exists() {
  command -v "$1" >/dev/null 2>&1
}

gettext_is_compatible() {
  command_exists msgfmt \
    && command_exists msgmerge \
    && msgmerge --help 2>&1 | grep -q -- '--previous'
}

generate_secret_key() {
  if command_exists python; then
    python - <<'PY'
import secrets

chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*(-_=+)"
print("".join(secrets.choice(chars) for _ in range(50)))
PY
    return
  fi

  if command_exists openssl; then
    openssl rand -base64 50
    return
  fi

  echo "change-me-in-production"
}

ensure_env_file() {
  if [[ -f .env ]]; then
    echo ".env already exists"
    return
  fi

  echo "Creating .env with development defaults"
  cat > .env <<EOF
ENV=LOCAL
DB_URL=postgresql://postgres:postgres@localhost:5432/postgres
SECRET_KEY=$(generate_secret_key)
REDIS_URL=redis://localhost:6379
LANGUAGE_CODE=vi
MINIO__ENDPOINT=localhost:9000
MINIO__ACCESS_KEY=minioadmin
MINIO__SECRET_KEY=minioadmin
MINIO__PUBLIC_BUCKET=public
MINIO__PRIVATE_BUCKET=private
EOF
}

install_gettext() {
  echo "GNU gettext msgfmt was not found. Attempting to install gettext."

  if command_exists apt-get; then
    sudo apt-get update
    sudo apt-get install -y gettext
    return
  fi

  if command_exists apk; then
    sudo apk add gettext
    return
  fi

  if command_exists pacman; then
    sudo pacman -S --needed gettext
    return
  fi

  if command_exists brew; then
    brew install gettext
    brew link --force gettext || true
    return
  fi

  if command_exists choco.exe; then
    choco.exe install gettext -y
    return
  fi

  if command_exists winget.exe; then
    winget.exe install --id mlocati.GetText -e --accept-package-agreements --accept-source-agreements
    return
  fi

  echo "Could not find a supported package manager to install GNU gettext." >&2
  echo "Install gettext manually, restart the terminal, then rerun this script." >&2
  return 1
}

ensure_gettext() {
  if gettext_is_compatible; then
    echo "GNU gettext is already compatible with Django"
    return 0
  fi

  if command_exists msgmerge; then
    echo "Existing gettext msgmerge is not compatible with Django makemessages." >&2
  fi

  install_gettext || return 1

  if gettext_is_compatible; then
    echo "GNU gettext is ready"
    return 0
  fi

  echo "GNU gettext was installed, but a compatible msgmerge is not available on PATH yet." >&2
  echo "If GnuWin32 appears before the new gettext install on PATH, remove it or move it later." >&2
  echo "Restart the terminal or update PATH, then rerun this script." >&2
  return 1
}

activate_venv() {
  if [[ -f .venv/bin/activate ]]; then
    # Linux/macOS
    # shellcheck disable=SC1091
    source .venv/bin/activate
    return
  fi

  if [[ -f .venv/Scripts/activate ]]; then
    # Windows Git Bash
    # shellcheck disable=SC1091
    source .venv/Scripts/activate
  fi
}

setup_local() {
  if ! command_exists python; then
    echo "Python is required for local setup." >&2
    exit 1
  fi

  ensure_env_file

  if [[ ! -d .venv ]]; then
    echo "Creating Python virtual environment"
    python -m venv .venv
  else
    echo ".venv already exists"
  fi

  activate_venv

  echo "Installing Python dependencies"
  python -m pip install --upgrade pip
  python -m pip install -r requirements.txt

  if ensure_gettext; then
    echo "Compiling translation catalogs"
    python manage.py compilemessages
  else
    echo "Skipping compilemessages because GNU gettext is not ready." >&2
  fi

  echo "Running migrations"
  python manage.py migrate

  cat <<'EOF'

Local setup complete.

Start the API:
  python manage.py runserver

Start the worker in another terminal:
  python manage.py run_huey
EOF
}

start_docker() {
  if ! command_exists docker; then
    echo "Docker is required for Docker setup." >&2
    exit 1
  fi

  ensure_env_file

  echo "Starting Docker development stack"
  docker compose up --build
}

case "$MODE" in
  docker)
    start_docker
    ;;
  local)
    setup_local
    ;;
  help|--help|-h)
    usage
    ;;
  *)
    echo "Unknown mode: $MODE" >&2
    usage >&2
    exit 1
    ;;
esac
