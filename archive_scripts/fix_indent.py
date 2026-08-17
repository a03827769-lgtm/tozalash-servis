import os

file_path = "bot/telegram_bot.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

bad_snippet_1 = """    if lang == 'uz':
        menu = get_main_menu_uz()
    elif lang == 'ru':
        menu = get_main_menu_ru()
        else:
            menu = get_main_menu_en()"""

good_snippet_1 = """    if lang == 'uz':
        menu = get_main_menu_uz()
    elif lang == 'ru':
        menu = get_main_menu_ru()
    else:
        menu = get_main_menu_en()"""

content = content.replace(bad_snippet_1, good_snippet_1)

bad_snippet_2 = """        if lang == 'uz':
            menu = get_main_menu_uz()
        elif lang == 'ru':
            menu = get_main_menu_ru()
        else:
            menu = get_main_menu_en()"""

good_snippet_2 = """        if lang == 'uz':
            menu = get_main_menu_uz()
        elif lang == 'ru':
            menu = get_main_menu_ru()
        else:
            menu = get_main_menu_en()"""

# Actually, the indentation for other instances was correct from the regex replacement, it was only the first one that was wrong initially.
# Let's just fix everything that looks like the bad indentation.

import re

# Match any indentation
pattern = re.compile(
    r"([ \t]+)if lang == 'uz':\n[ \t]+menu = get_main_menu_uz\(\)\n[ \t]+elif lang == 'ru':\n[ \t]+menu = get_main_menu_ru\(\)\n[ \t]+else:\n[ \t]+menu = get_main_menu_en\(\)"
)


def repl(match):
    indent = match.group(1)
    return f"{indent}if lang == 'uz':\n{indent}    menu = get_main_menu_uz()\n{indent}elif lang == 'ru':\n{indent}    menu = get_main_menu_ru()\n{indent}else:\n{indent}    menu = get_main_menu_en()"


content = pattern.sub(repl, content)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("Regex replace applied.")
