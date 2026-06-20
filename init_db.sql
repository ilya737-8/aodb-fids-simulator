CREATE TABLE IF NOT EXISTS airlines (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS flights (
    flight_num TEXT PRIMARY KEY,
    airline_code TEXT,
    destination TEXT NOT NULL,
    sched_time TEXT NOT NULL,
    status TEXT NOT NULL,
    FOREIGN KEY (airline_code) REFERENCES airlines(code)
);

CREATE TABLE IF NOT EXISTS fids_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    flight_num TEXT,
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    payload TEXT,
    status_code INTEGER
);

INSERT OR IGNORE INTO airlines (code, name) VALUES ('SU', 'Aeroflot'), ('S7', 'S7 Airlines');
INSERT OR IGNORE INTO flights (flight_num, airline_code, destination, sched_time, status)
VALUES
('SU-100', 'SU', 'Moscow', '12:00', 'Scheduled'),
('S7-2501', 'S7', 'Novosibirsk', '14:30', 'Check-in');