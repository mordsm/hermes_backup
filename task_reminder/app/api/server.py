from fastapi import FastAPI

app = FastAPI(title="Task Reminder API")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/today")
def today():
    # TODO: return v_today
    return []


@app.get("/overdue")
def overdue():
    # TODO: return v_overdue
    return []


@app.get("/backlog")
def backlog():
    # TODO: return v_stale_backlog plus active backlog
    return []
