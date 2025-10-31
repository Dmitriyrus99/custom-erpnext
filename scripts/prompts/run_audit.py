#!/usr/bin/env python3
import os
from openai import OpenAI

# --- Настройки ---
PROJECT_PATH = "/home/frappe/frappe-bench/frappe-bench"
PROMPT_FILE = f"{PROJECT_PATH}/scripts/prompts/audit_and_cleanup.txt"
OUTPUT_DIR = f"{PROJECT_PATH}/docs/audit"
MODEL = "gpt-5"  # при необходимости можно заменить на gpt-5-turbo

# --- Инициализация ---
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- Загрузка промта ---
with open(PROMPT_FILE, "r") as f:
    base_prompt = f.read()

# --- Список файлов проекта (ограничим глубину для ускорения) ---
project_files = []
for root, dirs, files in os.walk(PROJECT_PATH):
    if "node_modules" in root or "env" in root or ".git" in root:
        continue
    for file in files:
        rel = os.path.relpath(os.path.join(root, file), PROJECT_PATH)
        project_files.append(rel)
project_summary = "\n".join(project_files[:500])  # ограничим первичный список

# --- Формирование запроса ---
prompt = f"""{base_prompt}

📂 Проектная директория: {PROJECT_PATH}
Найдено файлов: {len(project_files)}

Список первых файлов для анализа:
{project_summary}

Начни выполнение с ЭТАПА 1 (Полный аудит и ревизия документации).
"""

# --- Запрос к GPT ---
print("🔍 Выполняется аудит проекта... Это может занять несколько минут.")
response = client.chat.completions.create(
    model=MODEL,
    messages=[
        {"role": "system", "content": "Ты — ведущий архитектор и инженер DevOps. Работаешь в изолированной песочнице, имеешь полный доступ к проекту."},
        {"role": "user", "content": prompt}
    ],
    temperature=1,
)

output = response.choices[0].message.content

# --- Сохранение результатов ---
outfile = f"{OUTPUT_DIR}/audit_report.md"
with open(outfile, "w") as f:
    f.write(output)

print(f"✅ Отчёт создан: {outfile}")
print("📘 Продолжи вручную следующие этапы: архитектура, план, CI/CD и очистка документации.")
