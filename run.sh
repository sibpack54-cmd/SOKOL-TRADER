#!/bin/bash
# SOKOL-TRADER v1.0 — Запуск для Linux
# Запускать из папки проекта: bash run.sh

# Путь к модулям
export PYTHONPATH="${PWD}/src"

# Заголовок
echo ""
echo "SOKOL-TRADER v1.0 starting..."
echo "==================================================="
echo ""

# Запуск
python src/scheduler.py

# Пауза, если упало
if [ $? -ne 0 ]; then
    echo ""
    echo "Error! Exit code: $?"
    echo "Press Enter to exit..."
    read
fi
