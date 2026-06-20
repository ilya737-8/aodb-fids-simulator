import sqlite3
import json
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import requests

app = FastAPI(title="AODB-FIDS Integration Gateway", version="1.0")
DB_NAME = "aodb.db"


# ==================== МОДЕЛИ ====================

class StatusUpdate(BaseModel):
    flight_num: str
    new_status: str


class FlightCreate(BaseModel):
    flight_num: str
    airline_code: str
    destination: str
    sched_time: str
    status: str = "Scheduled"


FIDS_WEBHOOK_URL = "https://httpbin.org/post"


def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        with open("init_db.sql", "r") as f:
            conn.executescript(f.read())


@app.on_event("startup")
def startup_event():
    init_db()


# ==================== API ====================

@app.get("/flights")
def get_flights():
    with sqlite3.connect(DB_NAME) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        rows = cursor.execute("SELECT * FROM flights").fetchall()
        return [dict(row) for row in rows]


@app.post("/flights")
def create_flight(data: FlightCreate):
    """Создание нового рейса"""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()

        airline = cursor.execute(
            "SELECT code FROM airlines WHERE code = ?",
            (data.airline_code,)
        ).fetchone()

        if not airline:
            raise HTTPException(status_code=400, detail="Авиакомпания не найдена")

        existing = cursor.execute(
            "SELECT flight_num FROM flights WHERE flight_num = ?",
            (data.flight_num,)
        ).fetchone()

        if existing:
            raise HTTPException(status_code=400, detail="Рейс с таким номером уже существует")

        cursor.execute("""
            INSERT INTO flights (flight_num, airline_code, destination, sched_time, status)
            VALUES (?, ?, ?, ?, ?)
        """, (
            data.flight_num,
            data.airline_code,
            data.destination,
            data.sched_time,
            data.status
        ))
        conn.commit()

        return {"status": "created", "flight_num": data.flight_num}


@app.post("/flights/update-status")
def update_flight_status(data: StatusUpdate):
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()

        flight = cursor.execute("SELECT * FROM flights WHERE flight_num = ?", (data.flight_num,)).fetchone()
        if not flight:
            raise HTTPException(status_code=404, detail="Flight not found")

        old_status = flight[4]  # status is 5th column (index 4)
        cursor.execute("UPDATE flights SET status = ? WHERE flight_num = ?", (data.new_status, data.flight_num))

        fids_payload = {
            "event": "FLIGHT_STATUS_CHANGED",
            "flight_num": data.flight_num,
            "old_status": old_status,
            "new_status": data.new_status
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


# ==================== HTML СТРАНИЦА ====================

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Информационная система управления аэровокзалом</title>
    <style>
        * { box-sizing: border-box; }
        body { font-family: 'Segoe UI', sans-serif; max-width: 1200px; margin: 20px auto; padding: 0 20px; background: #f0f4f8; }
        h1 { color: #1a365d; }
        .stats { display: flex; gap: 15px; margin: 20px 0; flex-wrap: wrap; }
        .stat-card { background: white; padding: 12px 20px; border-radius: 10px; box-shadow: 0 2px 6px rgba(0,0,0,0.06); }
        .stat-card h3 { margin: 0; font-size: 0.8rem; color: #718096; }
        .stat-card .value { font-size: 1.8rem; font-weight: 700; color: #2b6cb0; }
        table { width: 100%; border-collapse: collapse; background: white; border-radius: 10px; overflow: hidden; box-shadow: 0 2px 6px rgba(0,0,0,0.06); }
        th { background: #f7fafc; text-align: left; padding: 10px 15px; font-weight: 600; border-bottom: 2px solid #e2e8f0; }
        td { padding: 8px 15px; border-bottom: 1px solid #edf2f7; }
        tr:hover { background: #f7fafc; }
        .status { display: inline-block; padding: 2px 12px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; }
        .status-Scheduled { background: #ebf8ff; color: #2b6cb0; }
        .status-Check-in { background: #fefcbf; color: #975a16; }
        .status-Boarding { background: #f6e05e; color: #744210; }
        .status-Departed { background: #c6f6d5; color: #22543d; }
        .status-Delayed { background: #fed7d7; color: #9b2c2c; }
        .status-Cancelled { background: #e2e8f0; color: #4a5568; }
        .btn { padding: 5px 12px; border: none; border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 0.85rem; }
        .btn-primary { background: #2b6cb0; color: white; }
        .btn-primary:hover { background: #1a365d; }
        .btn-success { background: #38a169; color: white; }
        .btn-success:hover { background: #2f855a; }
        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); align-items: center; justify-content: center; z-index: 1000; }
        .modal.open { display: flex; }
        .modal-content { background: white; padding: 25px; border-radius: 14px; max-width: 400px; width: 90%; }
        .modal-content h2 { margin-top: 0; }
        .close { float: right; font-size: 1.8rem; cursor: pointer; color: #a0aec0; }
        .close:hover { color: #2d3748; }
        select, input { width: 100%; padding: 8px 10px; border: 1px solid #e2e8f0; border-radius: 6px; font-size: 1rem; margin: 5px 0 12px; }
        .toast { position: fixed; bottom: 20px; right: 20px; padding: 10px 20px; border-radius: 10px; color: white; font-weight: 500; opacity: 0; transform: translateY(20px); transition: all 0.3s; z-index: 2000; }
        .toast.show { opacity: 1; transform: translateY(0); }
        .toast.success { background: #38a169; }
        .toast.error { background: #e53e3e; }
        .header { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; }
        .actions { display: flex; gap: 8px; flex-wrap: wrap; }
    </style>
</head>
<body>

<h1>✈️ Информационная система управления аэровокзалом</h1>
<p style="color: #4a5568;">AODB — FIDS Integration Gateway | Учебная практика 2026</p>

<div class="stats" id="stats">
    <div class="stat-card"><h3>Всего рейсов</h3><div class="value" id="statTotal">—</div></div>
    <div class="stat-card"><h3>✅ Выполнено</h3><div class="value" id="statDeparted">—</div></div>
    <div class="stat-card"><h3>⏳ Активные</h3><div class="value" id="statActive">—</div></div>
    <div class="stat-card"><h3>⚠️ Задержано</h3><div class="value" id="statDelayed">—</div></div>
</div>

<div class="header">
    <h2>📋 Список рейсов</h2>
    <div class="actions">
        <button class="btn btn-success" onclick="openCreate()">+ Добавить рейс</button>
        <button class="btn btn-primary" onclick="loadFlights()">🔄 Обновить</button>
    </div>
</div>

<table>
    <thead>
        <tr>
            <th>Рейс</th>
            <th>Авиакомпания</th>
            <th>Назначение</th>
            <th>Время</th>
            <th>Статус</th>
            <th>Действие</th>
        </tr>
    </thead>
    <tbody id="flightsBody">
        <tr><td colspan="6" style="text-align:center;color:#a0aec0;padding:30px;">⏳ Загрузка...</td></tr>
    </tbody>
</table>

<!-- Модалка статуса -->
<div class="modal" id="statusModal">
    <div class="modal-content">
        <span class="close" onclick="closeModal('statusModal')">&times;</span>
        <h2>Изменить статус</h2>
        <p id="statusInfo" style="color:#718096;"></p>
        <form id="statusForm">
            <input type="hidden" id="statusFlightNum">
            <select id="statusSelect">
                <option value="Scheduled">Запланирован</option>
                <option value="Check-in">Регистрация</option>
                <option value="Boarding">Посадка</option>
                <option value="Last Call">Последнее приглашение</option>
                <option value="Departed">Вылетел</option>
                <option value="Delayed">Задержан</option>
                <option value="Cancelled">Отменен</option>
            </select>
            <button type="submit" class="btn btn-primary" style="width:100%;">Обновить</button>
        </form>
    </div>
</div>

<!-- Модалка создания -->
<div class="modal" id="createModal">
    <div class="modal-content">
        <span class="close" onclick="closeModal('createModal')">&times;</span>
        <h2>Добавить рейс</h2>
        <form id="createForm">
            <input type="text" id="newFlightNum" placeholder="Номер рейса (SU-100)" required>
            <input type="text" id="newAirline" placeholder="Код а/к (SU, S7)" required>
            <input type="text" id="newDestination" placeholder="Назначение" required>
            <input type="time" id="newSchedTime" required>
            <button type="submit" class="btn btn-success" style="width:100%;">Создать</button>
        </form>
    </div>
</div>

<div class="toast" id="toast"></div>

<script>
async function loadFlights() {
    try {
        const res = await fetch('/flights');
        if (!res.ok) throw new Error('HTTP ' + res.status);
        const flights = await res.json();
        renderFlights(flights);
        updateStats(flights);
    } catch (e) {
        document.getElementById('flightsBody').innerHTML = '<tr><td colspan="6" style="text-align:center;color:#e53e3e;">❌ Ошибка: ' + e.message + '</td></tr>';
    }
}

function renderFlights(flights) {
    const tbody = document.getElementById('flightsBody');
    if (!flights || flights.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;color:#a0aec0;padding:30px;">Нет рейсов</td></tr>';
        return;
    }
    tbody.innerHTML = flights.map(f => `
        <tr>
            <td><strong>${f.flight_num}</strong></td>
            <td>${f.airline_code || '—'}</td>
            <td>${f.destination}</td>
            <td>${f.sched_time}</td>
            <td><span class="status status-${f.status}">${f.status}</span></td>
            <td><button class="btn btn-primary" onclick="openStatus('${f.flight_num}', '${f.status}')">Изменить</button></td>
        </tr>
    `).join('');
}

function updateStats(flights) {
    document.getElementById('statTotal').textContent = flights.length;
    document.getElementById('statDeparted').textContent = flights.filter(f => f.status === 'Departed').length;
    document.getElementById('statActive').textContent = flights.filter(f => ['Scheduled','Check-in','Boarding','Last Call'].includes(f.status)).length;
    document.getElementById('statDelayed').textContent = flights.filter(f => f.status === 'Delayed').length;
}

function openStatus(flightNum, currentStatus) {
    document.getElementById('statusFlightNum').value = flightNum;
    document.getElementById('statusInfo').textContent = 'Рейс ' + flightNum + ' (сейчас: ' + currentStatus + ')';
    document.getElementById('statusSelect').value = currentStatus;
    document.getElementById('statusModal').classList.add('open');
}

function openCreate() {
    document.getElementById('createModal').classList.add('open');
}

function closeModal(id) {
    document.getElementById(id).classList.remove('open');
}

document.querySelectorAll('.modal').forEach(m => {
    m.addEventListener('click', function(e) {
        if (e.target === this) this.classList.remove('open');
    });
});

document.getElementById('statusForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    const flightNum = document.getElementById('statusFlightNum').value;
    const newStatus = document.getElementById('statusSelect').value;
    try {
        const res = await fetch('/flights/update-status', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ flight_num: flightNum, new_status: newStatus })
        });
        const data = await res.json();
        if (res.ok) {
            showToast('✅ Статус изменен на ' + newStatus, 'success');
            closeModal('statusModal');
            loadFlights();
        } else {
            showToast('❌ Ошибка: ' + (data.detail || 'неизвестно'), 'error');
        }
    } catch (e) {
        showToast('❌ Ошибка соединения', 'error');
    }
});

document.getElementById('createForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    const data = {
        flight_num: document.getElementById('newFlightNum').value.trim(),
        airline_code: document.getElementById('newAirline').value.trim(),
        destination: document.getElementById('newDestination').value.trim(),
        sched_time: document.getElementById('newSchedTime').value,
        status: 'Scheduled'
    };
    if (!data.flight_num || !data.airline_code || !data.destination || !data.sched_time) {
        showToast('❌ Заполните все поля', 'error');
        return;
    }
    try {
        const res = await fetch('/flights', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (res.ok) {
            showToast('✅ Рейс создан!', 'success');
            closeModal('createModal');
            this.reset();
            loadFlights();
        } else {
            const err = await res.json();
            showToast('❌ ' + (err.detail || 'Ошибка'), 'error');
        }
    } catch (e) {
        showToast('❌ Ошибка соединения', 'error');
    }
});

function showToast(msg, type) {
    const t = document.getElementById('toast');
    t.textContent = msg;
    t.className = 'toast ' + type;
    t.classList.add('show');
    clearTimeout(t._timer);
    t._timer = setTimeout(() => t.classList.remove('show'), 4000);
}

loadFlights();
setInterval(loadFlights, 15000);
</script>

</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
def index():
    """Главная страница с интерфейсом"""
    return HTMLResponse(HTML_PAGE)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)