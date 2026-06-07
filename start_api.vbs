Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\Users\User\Desktop\telegram-ad-exchange\backend"
WshShell.Run "cmd /c C:\Users\User\Desktop\telegram-ad-exchange\backend\venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8001", 0, False
WshShell.Run "cmd /c C:\Users\User\Desktop\telegram-ad-exchange\backend\venv\Scripts\python.exe -m bot.main", 0, False
