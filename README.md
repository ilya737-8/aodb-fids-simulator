# ✈️ Информационная система управления аэровокзалом

**AODB — FIDS Integration Gateway**

Демонстрационный проект для учебной практики по теме «Информационная система управления аэровокзалом».

---

## 📋 О проекте

Проект представляет собой прототип информационной системы управления аэровокзалом, реализующей интеграцию между:

- **AODB** (Airport Operational Database) — операционная база данных аэропорта
- **FIDS** (Flight Information Display System) — система визуального информирования пассажиров

Система позволяет:
- Просматривать список рейсов
- Создавать новые рейсы
- Изменять статусы рейсов
- Отправлять уведомления об изменениях во внешнюю систему FIDS
- Просматривать логи отправки уведомлений

---

## 🚀 Быстрый старт

### Требования
- Python 3.8 или выше

### Установка и запуск

```bash
# 1. Клонируйте репозиторий
git clone https://github.com/ваш-репозиторий/aodb-fids-simulator.git
cd aodb-fids-simulator

# 2. Установите зависимости
pip install -r requirements.txt

# 3. Запустите сервер
python app.py

# 4. Откройте в браузере
http://localhost:8000/

```
---

## 📂 Структура проекта

aodb-fids-simulator/
│
├── app.py              # Главный файл приложения (FastAPI + HTML)
├── init_db.sql         # Скрипт инициализации базы данных
├── requirements.txt    # Зависимости Python
├── README.md           # Документация
└── aodb.db             # Файл базы данных (создаётся автоматически)

## 🛠 Технологии

Компонент	Технология
Бэкенд	Python + FastAPI
База данных	SQLite
Фронтенд	HTML + CSS + JavaScript
HTTP-клиент	requests

## 📡 API Endpoints

Метод	URL	Описание
GET	/	Веб-интерфейс
GET	/flights	Список всех рейсов
POST	/flights	Создание нового рейса
POST	/flights/update-status	Изменение статуса рейса
GET	/docs	Документация API (Swagger)

## 📊 Статусы рейсов

Статус	Описание
Scheduled	Запланирован
Check-in	Регистрация
Boarding	Посадка
Last Call	Последнее приглашение
Departed	Вылетел
Delayed	Задержан
Cancelled	Отменен

## 🗄️ Структура базы данных
### Таблица airlines
```
Поле	Тип	                Описание
code	TEXT PRIMARY KEY	Код авиакомпании
name	TEXT NOT NULL	        Название авиакомпании
```
### Таблица flights
```
Поле	        Тип	                Описание
flight_num	TEXT PRIMARY KEY	Номер рейса
airline_code	TEXT FOREIGN KEY	Код авиакомпании
destination	TEXT NOT NULL	        Назначение
sched_time	TEXT NOT NULL	        Время вылета
status	        TEXT NOT NULL	        Текущий статус
```
### Таблица fids_logs
```
Поле	        Тип	                Описание
log_id	        INTEGER PRIMARY KEY	ID записи
flight_num	TEXT	                Номер рейса
sent_at	        TIMESTAMP	        Время отправки
payload	        TEXT	                Отправленные данные
status_code	INTEGER	HTTP            статус ответа
```
## 🧪 Тестовые данные
При первом запуске автоматически создаются:
```
Рейс	  Авиакомпания	    Назначение	Время	Статус
SU-100	  SU (Aeroflot)	    Moscow	12:00	Scheduled
S7-2501	  S7 (S7 Airlines)  Novosibirsk	14:30	Check-in
Доступные авиакомпании: SU, S7, UT, U6
```

## 🔧 Устранение неполадок
### ❌ ModuleNotFoundError: No module named 'fastapi'
```
bash
pip install -r requirements.txt
```
### ❌ Address already in use (порт 8000 занят)

```bash
python -m uvicorn app:app --port 8001
```
### ❌ sqlite3.OperationalError: no such table: flights
```
Убедитесь, что файл init_db.sql находится в папке проекта. База данных создаётся автоматически при первом запуске.
```
### ⚠️ DeprecationWarning: on_event is deprecated
Это предупреждение, а не ошибка. Код работает корректно. Можете игнорировать.

🏗️ Архитектура системы

---



## 🔄 Поток данных

### 1. Просмотр рейсов
Браузер → GET /flights → FastAPI → SQLite → JSON → Браузер


### 2. Создание рейса
Браузер → POST /flights → FastAPI → Валидация → SQLite → JSON → Браузер


### 3. Изменение статуса
Браузер → POST /flights/update-status → FastAPI → Обновление SQLite
│
▼
Отправка в FIDS
│
▼
Запись в fids_logs
│
▼
JSON-ответ → Браузер


---

## 📁 Физическая структура

aodb-fids-simulator/
│
├── app.py # 🚀 Главный файл (FastAPI + встроенный HTML)
├── init_db.sql # 📋 Скрипт инициализации БД
├── requirements.txt # 📦 Зависимости Python
├── README.md # 📄 Документация
└── aodb.db # 🗄️ База данных SQLite (создаётся автоматически)


---

## 🔧 Стек технологий

| Уровень | Технология | Назначение |
|---------|-----------|------------|
| **Фронтенд** | HTML + CSS + JavaScript | Веб-интерфейс |
| **API** | FastAPI | REST API + документация Swagger |
| **Бизнес-логика** | Python | Обработка запросов, валидация |
| **Хранилище** | SQLite | База данных аэропорта |
| **HTTP-клиент** | requests | Отправка уведомлений в FIDS |

👤 Автор

Студент	Гусаров Илья Максимович

Группа	УБВТ2404

Направление	09.03.01 «Информатика и вычислительная техника»

Профиль	«Организация и технологии защиты информации»

Кафедра	Программная инженерия

Год	2026
