import re

with open("database_new.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if (
        line.startswith("            ")
        and not line.startswith("                ")
        and not line.startswith("            yield conn")
    ):
        # Add 4 spaces
        new_lines.append("    " + line)
    else:
        new_lines.append(line)

code = "".join(new_lines)
code = code.replace(
    "                    async with conn.cursor() as cursor:",
    "            async with conn.cursor() as cursor:",
)
code = code.replace(" as cursor:", "")
code = code.replace("strftime('%Y-%m', date)", "DATE_FORMAT(date, '%Y-%m')")
code = code.replace("strftime('%Y-%m', 'now')", "DATE_FORMAT(CURDATE(), '%Y-%m')")
# Wait, replacing all 12 spaces with 16 is dangerous if it hits `async with conn.cursor() as cursor:` which SHOULD be 12.
# So I replace `async with conn.cursor() as cursor:` back to 12.

with open("database.py", "w", encoding="utf-8") as f:
    f.write(code)
