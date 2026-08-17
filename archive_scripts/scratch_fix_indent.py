with open("database.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

out = []
in_cursor_block = False
base_indent = ""

for i, line in enumerate(lines):
    # Detect the start of `async with conn.cursor() as cursor:`
    if "async with conn.cursor() as cursor:" in line:
        out.append(line)
        in_cursor_block = True
        base_indent = line[: len(line) - len(line.lstrip())]
        continue

    # If we are in the block and the line is not empty
    if in_cursor_block and line.strip() != "":
        # Determine the current indentation
        current_indent = line[: len(line) - len(line.lstrip())]
        # If the current indent is <= base_indent, we exited the block
        if len(current_indent) <= len(base_indent) and not line.strip().startswith("#"):
            in_cursor_block = False
            out.append(line)
            continue

        # If we are in the block and it's not indented past base_indent (due to previous bad regex replacement)
        if len(current_indent) <= len(base_indent):
            # It's inside the block but missing 4 spaces
            out.append("    " + line)
        else:
            # It already has some indentation, let's just make sure it's at least base_indent + 4
            # Actually, the regex replacement didn't touch the lines after the first one.
            # E.g. in `init_db`, all lines were already at `base_indent` (from async with get_conn() as conn)
            # So they are exactly at len(base_indent).
            # If so, add 4 spaces.
            if len(current_indent) == len(base_indent):
                out.append("    " + line)
            else:
                # E.g. inside the query string, which is already indented more, we can leave it or indent it.
                # Since it's a multiline string, we can just add 4 spaces to everything that is not an empty line.
                out.append("    " + line)
    else:
        out.append(line)

with open("database.py", "w", encoding="utf-8") as f:
    f.writelines(out)
