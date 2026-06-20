import sqlite3
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests

app = FastAPI(title="AODB-FIDS Integration Gateway", version="1.0")
DB_NAME = "aodb.db"


class StatusUpdate(BaseModel):
    flight_num: str
    new_status: str


FIDS_WEBHOOK_URL = "https://httpbin.org/post"


def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        with open("init_db.sql", "r") as f:
            conn.executescript(f.read())


@app.on_event("startup")
def startup_event():
    init_db()


@app.get("/flights")
def get_flights():
    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        rows = cursor.execute("SELECT * FROM flights").fetchall()
        return [dict(row) for row in rows]


@app.post("/flights/update-status")
def update_flight_status(data: StatusUpdate):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()

        flight = cursor.execute("SELECT * FROM flights WHERE flight_num = ?", (data.flight_num,)).fetchone()
        if not flight:
            raise HTTPException(status_code=404, detail="Flight not found")

        cursor.execute("UPDATE flights SET status = ? WHERE flight_num = ?", (data.new_status, data.flight_num))

        fids_payload = {
            "event": "FLIGHT_STATUS_CHANGED",
            "flight_num": data.flight_num,
            "status": data.new_status
        }

        try:
            response = requests.post(FIDS_WEBHOOK_URL, json=fids_payload, timeout=5)
            status_code = response.status_code
        except requests.RequestException:
            status_code = 500

        cursor.execute(
            "INSERT INTO fids_logs (flight_num, payload, status_code) VALUES (?, ?, ?)",
            (data.flight_num, json.dumps(fids_payload), status_code)
        )
        conn.commit()

    return {
        "status": "Success",
        "aodb_updated": True,
        "fids_notification_status": status_code
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)