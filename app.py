"""Strength Log: a local workout journal with a JSON API and SQLite storage."""
import json
import math
import re
import sqlite3
from contextlib import closing
from datetime import date
from pathlib import Path
from wsgiref.simple_server import make_server

ROOT = Path(__file__).resolve().parent
DATABASE = ROOT / "strength.sqlite3"
ASSETS = {
    "/": ("index.html", "text/html"),
    "/style.css": ("style.css", "text/css"),
    "/app.js": ("app.js", "text/javascript"),
}


def connect():
    db = sqlite3.connect(DATABASE, timeout=5)
    db.row_factory = sqlite3.Row
    db.execute("""CREATE TABLE IF NOT EXISTS sets (
        id INTEGER PRIMARY KEY, day TEXT NOT NULL, exercise TEXT NOT NULL,
        reps INTEGER NOT NULL, weight REAL NOT NULL
    )""")
    return db


def read_set(env):
    length = int(env.get("CONTENT_LENGTH") or 0)
    if not 0 < length <= 8192:
        raise ValueError("Submit a set smaller than 8 KB.")
    try:
        data = json.loads(env["wsgi.input"].read(length))
    except (ValueError, UnicodeError):
        raise ValueError("Send valid JSON.") from None
    if not isinstance(data, dict):
        raise ValueError("Send a set with a date, exercise, reps, and weight.")
    day = data.get("day")
    if not isinstance(day, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", day):
        raise ValueError("Use a date in YYYY-MM-DD format.")
    date.fromisoformat(day)
    exercise = data.get("exercise")
    if not isinstance(exercise, str) or not 1 <= len(exercise.strip()) <= 80:
        raise ValueError("Enter an exercise name between 1 and 80 characters.")
    reps, weight = data.get("reps"), data.get("weight")
    if type(reps) is not int or not 1 <= reps <= 1000:
        raise ValueError("Enter between 1 and 1,000 whole reps.")
    if type(weight) not in (float, int) or not 0 <= weight <= 10000 or not math.isfinite(weight):
        raise ValueError("Enter a weight from 0 to 10,000 lb.")
    return day, exercise.strip(), reps, weight


def api(env, method, item):
    with closing(connect()) as db, db:
        if method == "GET" and item is None:
            rows = db.execute("SELECT * FROM sets ORDER BY day DESC, id DESC")
            return "200 OK", [dict(row) for row in rows]
        if method == "POST" and item is None:
            values = read_set(env)
            cursor = db.execute("INSERT INTO sets(day,exercise,reps,weight) VALUES(?,?,?,?)", values)
            return "201 Created", {"id": cursor.lastrowid}
        if item is not None and method in ("PUT", "DELETE"):
            if method == "PUT":
                values = read_set(env)
                cursor = db.execute("UPDATE sets SET day=?,exercise=?,reps=?,weight=? WHERE id=?", (*values, item))
            else:
                cursor = db.execute("DELETE FROM sets WHERE id=?", (item,))
            if cursor.rowcount == 0:
                return "404 Not Found", {"error": "This set no longer exists."}
            return "200 OK", {"id": item}
        return "405 Method Not Allowed", {"error": "Method unavailable for this route."}


def application(env, start_response):
    path, method = env["PATH_INFO"], env["REQUEST_METHOD"]
    if method == "GET" and path in ASSETS:
        filename, mime = ASSETS[path]
        body = (ROOT / "web" / filename).read_bytes()
        status = "200 OK"
    else:
        mime = "application/json"
        route = re.fullmatch(r"/api/sets(?:/([1-9][0-9]{0,17}))?", path)
        try:
            if route:
                item = int(route[1]) if route[1] else None
                status, result = api(env, method, item)
            else:
                status, result = "404 Not Found", {"error": "Page not found."}
        except ValueError as exc:
            status, result = "400 Bad Request", {"error": str(exc)}
        except sqlite3.Error:
            status, result = "503 Service Unavailable", {"error": "Database unavailable. Try again."}
        body = json.dumps(result).encode()
    start_response(status, [("Content-Type", mime + "; charset=utf-8"),
                            ("Content-Length", str(len(body))), ("Cache-Control", "no-store")])
    return [body]


if __name__ == "__main__":
    print("Open http://127.0.0.1:8000 in your browser. Press Ctrl+C to stop.", flush=True)
    with make_server("127.0.0.1", 8000, application) as server:
        server.serve_forever()
