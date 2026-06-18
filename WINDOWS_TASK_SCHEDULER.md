# Windows Task Scheduler Setup

Use this command as the scheduled action:

```powershell
cd C:\path\to\task-reminder
.\.venv\Scripts\taskreminder.exe run-once
```

Recommended trigger:

- Start: at logon or a fixed time
- Repeat task every: 1 hour for MVP
- Later: every 15 minutes if precise reminders are needed

Important:

- If using Windows Toast notifications, run only when the user is logged in.
- If using Telegram/email, it can run without an interactive desktop session.
