#!/usr/bin/env bash
set -e

# Отримуємо абсолютний шлях до поточної папки
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ICON_PATH="$DIR/public/icon.svg"
LAUNCHER_SCRIPT="$DIR/Launch-App.sh"

echo "==================================================================="
echo "  🚀 Встановлення іконки AI Prospecting Agent (Fedora / Linux)"
echo "==================================================================="
echo ""

# 1. Перевірка Python 3
if ! command -v python3 &> /dev/null; then
    echo "[ПОМИЛКА] Python 3 не знайдено на вашій системі Fedora!"
    echo "Встановіть Python 3 через DNF:"
    echo "   sudo dnf install -y python3 python3-pip"
    echo ""
    exit 1
fi

echo "[1/4] Python версія: $(python3 --version)"

# 2. Переконуємось у наявності .env
if [ ! -f "$DIR/.env" ] && [ -f "$DIR/.env.example" ]; then
    cp "$DIR/.env.example" "$DIR/.env"
fi

# 3. Робимо виконуваними файли запуску
chmod -R +x "$DIR"/*.sh 2>/dev/null || true

# 4. Реєстрація системної іконки для Fedora / GNOME Shell
ICON_DIR="$HOME/.local/share/icons/hicolor/scalable/apps"
mkdir -p "$ICON_DIR"
cp "$ICON_PATH" "$ICON_DIR/ai-prospecting-agent.svg" 2>/dev/null || true
if command -v gtk-update-icon-cache &> /dev/null; then
    gtk-update-icon-cache -f -t "$HOME/.local/share/icons/hicolor" 2>/dev/null || true
fi

# 5. Створення .desktop файлу
DESKTOP_ENTRY="[Desktop Entry]
Version=1.0
Type=Application
Name=AI Prospecting Agent
GenericName=B2B Lead Intelligence Agent
Comment=Автономний B2B агент проспектингу та акаунт-розвідки (Python Flet)
Exec=bash \"$DIR/Launch-App.sh\"
Icon=$ICON_DIR/ai-prospecting-agent.svg
Path=$DIR
Terminal=false
StartupNotify=true
Categories=Office;Development;Network;
Keywords=AI;Prospecting;B2B;Sales;Lead;Intelligence;
StartupWMClass=flet
"

# Встановлюємо в системні меню користувача
APPS_DIR="$HOME/.local/share/applications"
mkdir -p "$APPS_DIR"
echo "$DESKTOP_ENTRY" > "$APPS_DIR/ai-prospecting-agent.desktop"
chmod +x "$APPS_DIR/ai-prospecting-agent.desktop"

# Також копіюємо ярлик на робочий стіл (якщо папка існує)
for DESKTOP_DIR in "$HOME/Desktop" "$HOME/Pulpit" "$HOME/Стільниця" "$HOME/Рабочий стол"; do
    if [ -d "$DESKTOP_DIR" ]; then
        echo "$DESKTOP_ENTRY" > "$DESKTOP_DIR/AI-Prospecting-Agent.desktop"
        chmod +x "$DESKTOP_DIR/AI-Prospecting-Agent.desktop"
        if command -v gio &> /dev/null; then
            gio set "$DESKTOP_DIR/AI-Prospecting-Agent.desktop" metadata::trusted true 2>/dev/null || true
        fi
    fi
done

# Оновлення бази даних додатків
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
fi

echo ""
echo "==================================================================="
echo "  ✅ УСПІШНО ВСТАНОВЛЕНО!"
echo "  Тепер додаток з'явився у системному меню програм GNOME / Fedora."
echo "  Ви можете знайти його, натиснувши Super (Win) і ввівши 'AI'."
echo "==================================================================="
