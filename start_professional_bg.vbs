Set WshShell = CreateObject("WScript.Shell")

' 1. Start Python API Backend hidden in background
WshShell.Run "cmd /c cd c:\Users\victus\Desktop\avtomatizatsiya\tozalash_servis && new_venv\Scripts\python.exe -X utf8 main.py > api_bg.log 2>&1", 0, False

' 2. Start Next.js Admin Panel hidden in background
WshShell.Run "cmd /c cd c:\Users\victus\Desktop\avtomatizatsiya\tozalash_servis\admin_panel && npm run dev > admin_bg.log 2>&1", 0, False
