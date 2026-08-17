import re

with open("database_new.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if "await cursor.execute" in line and " as cursor:" in line:
        line = line.replace(" as cursor:", "")
    new_lines.append(line)

code = "".join(new_lines)
# Also fix indentation
code = code.replace(
    "            async with conn.cursor() as cursor:\n            await cursor.execute",
    "            async with conn.cursor() as cursor:\n                await cursor.execute",
)
code = code.replace(
    "            async with conn.cursor() as cursor:\n            today",
    "            async with conn.cursor() as cursor:\n                today",
)
code = code.replace(
    "            async with conn.cursor() as cursor:\n            updates",
    "            async with conn.cursor() as cursor:\n                updates",
)
code = code.replace(
    "            async with conn.cursor() as cursor:\n            if worker_ids:",
    "            async with conn.cursor() as cursor:\n                if worker_ids:",
)
code = code.replace(
    "            async with conn.cursor() as cursor:\n            context_json",
    "            async with conn.cursor() as cursor:\n                context_json",
)

# Some strftime syntax inside the query needs fixing for MySQL:
# SUM(CASE WHEN type = 'daromad' AND strftime('%Y-%m', date) = strftime('%Y-%m', 'now')
code = code.replace("strftime('%Y-%m', date)", "DATE_FORMAT(date, '%Y-%m')")
code = code.replace("strftime('%Y-%m', 'now')", "DATE_FORMAT(CURDATE(), '%Y-%m')")

with open("database.py", "w", encoding="utf-8") as f:
    f.write(code)
