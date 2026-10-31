#!/usr/bin/env bash

# Переходимо в каталог зі скриптом
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

# Якщо передано прапорець --web, вмикаємо режим веб-сервера без помилок дисплею
if [[ "$*" == *"--web"* ]] || [[ "$*" == *"-w"* ]]; then
    export FLET_FORCE_WEB_SERVER=true
fi

# Запускаємо Python-версію додатку Flet
if [ -d ".venv" ]; then
    source .venv/bin/activate
    python3 main.py "$@"
else
    exit 1
fi
