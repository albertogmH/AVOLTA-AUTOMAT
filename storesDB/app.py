"""Basic CRUD web UI for the enriched stores SQLite database.

Run:  python storesDB/app.py   ->  http://127.0.0.1:5000
"""
import os
import signal
import socket
import subprocess
import time
import sqlite3
from urllib.parse import urlparse
from flask import Flask, request, jsonify, render_template

BASE_DIR = os.path.dirname(__file__)
DB_PATH = os.path.join(BASE_DIR, 'stores.db')


def derive_language(store_url):
    """Language code is the first path segment of the store URL (/es/, /en/...)."""
    if not store_url:
        return None
    path = urlparse(str(store_url)).path.strip("/").split("/")
    seg = path[0] if path and path[0] else None
    if seg and seg.isalpha() and 2 <= len(seg) <= 3:
        return seg.lower()
    return None

# Columns the UI can read/write (id is managed by SQLite).
FIELDS = [
    "division", "store_id", "code", "name", "website_id", "store_url",
    "website_name", "website_code", "website_url", "has_active_store",
    "iata_code", "country", "region",
]
FILTER_FIELDS = ["division", "region", "country", "has_active_store"]

app = Flask(__name__)


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/filters")
def api_filters():
    conn = get_db()
    result = {}
    for field in FILTER_FIELDS:
        rows = conn.execute(
            f"SELECT DISTINCT {field} AS v FROM stores "
            f"WHERE {field} IS NOT NULL AND {field} != '' ORDER BY {field}"
        ).fetchall()
        values = [r["v"] for r in rows]
        if field == "division":
            # Sort divisions numerically (1, 2, ... 10) instead of as text.
            values.sort(key=lambda v: (0, int(v)) if str(v).isdigit() else (1, str(v)))
        result[field] = values

    # Languages are derived from the store URL, not a stored column.
    lang_rows = conn.execute(
        "SELECT DISTINCT store_url FROM stores WHERE store_url IS NOT NULL AND store_url != ''"
    ).fetchall()
    langs = sorted({derive_language(r["store_url"]) for r in lang_rows} - {None})
    result["language"] = langs
    conn.close()
    return jsonify(result)


@app.route("/api/stores")
def api_list():
    conn = get_db()
    where, params = [], []

    search = request.args.get("search", "").strip()
    if search:
        like = f"%{search}%"
        cols = ["name", "code", "store_url", "website_name", "website_code",
                "website_url", "iata_code", "country", "region", "division"]
        where.append("(" + " OR ".join(f"{c} LIKE ?" for c in cols) + ")")
        params.extend([like] * len(cols))

    for field in FILTER_FIELDS:
        # Accept repeated params (field=a&field=b) and comma-separated values.
        values = []
        for raw in request.args.getlist(field):
            values.extend(v.strip() for v in raw.split(",") if v.strip())
        if values:
            placeholders = ", ".join(["?"] * len(values))
            where.append(f"{field} IN ({placeholders})")
            params.extend(values)

    # Active switch: "1" -> only active, "0" -> only non-active (incl. empty).
    active = request.args.get("active")
    if active == "1":
        where.append("has_active_store = 'Active'")
    elif active == "0":
        where.append("(has_active_store IS NULL OR has_active_store != 'Active')")

    sql = "SELECT * FROM stores"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY division, store_id"

    rows = conn.execute(sql, params).fetchall()
    conn.close()

    # Derive language per row and optionally filter by it (values from URL).
    lang_filter = []
    for raw in request.args.getlist("language"):
        lang_filter.extend(v.strip() for v in raw.split(",") if v.strip())
    lang_filter = set(lang_filter)

    result = []
    for r in rows:
        d = dict(r)
        d["language"] = derive_language(d.get("store_url"))
        if lang_filter and d["language"] not in lang_filter:
            continue
        result.append(d)
    return jsonify(result)


@app.route("/api/stores", methods=["POST"])
def api_create():
    data = request.get_json(force=True)
    values = [data.get(f) for f in FIELDS]
    conn = get_db()
    cur = conn.execute(
        f"INSERT INTO stores ({', '.join(FIELDS)}) "
        f"VALUES ({', '.join(['?'] * len(FIELDS))})",
        values,
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return jsonify({"id": new_id}), 201


@app.route("/api/stores/<int:store_pk>", methods=["PUT"])
def api_update(store_pk):
    data = request.get_json(force=True)
    values = [data.get(f) for f in FIELDS]
    conn = get_db()
    conn.execute(
        f"UPDATE stores SET {', '.join(f'{f} = ?' for f in FIELDS)} WHERE id = ?",
        values + [store_pk],
    )
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


@app.route("/api/stores/<int:store_pk>", methods=["DELETE"])
def api_delete(store_pk):
    conn = get_db()
    conn.execute("DELETE FROM stores WHERE id = ?", (store_pk,))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})


def kill_previous_instances():
    """Kill other python processes running this same app.py (old servers)."""
    script = os.path.abspath(__file__)
    try:
        out = subprocess.run(["pgrep", "-f", script],
                             capture_output=True, text=True).stdout
    except FileNotFoundError:
        return
    for pid in out.split():
        pid = int(pid)
        if pid != os.getpid():
            try:
                os.kill(pid, signal.SIGKILL)
                print(f" * Instancia previa eliminada (pid {pid})")
            except ProcessLookupError:
                pass


def free_port(port, host="127.0.0.1"):
    """Kill whatever process is listening on the given port."""
    try:
        out = subprocess.run(["lsof", "-ti", f"tcp:{port}"],
                             capture_output=True, text=True).stdout
    except FileNotFoundError:
        return
    for pid in out.split():
        pid = int(pid)
        if pid != os.getpid():
            try:
                os.kill(pid, signal.SIGKILL)
                print(f" * Proceso en el puerto {port} eliminado (pid {pid})")
            except ProcessLookupError:
                pass


def port_is_free(port, host="127.0.0.1"):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        return sock.connect_ex((host, port)) != 0


def wait_port_free(port, host="127.0.0.1", timeout=3.0):
    """Wait until the port is released after killing its process."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if port_is_free(port, host):
            return True
        time.sleep(0.1)
    return port_is_free(port, host)


def find_free_port(preferred=5000, host="127.0.0.1", attempts=20):
    """Return the preferred port if free, otherwise the next available one."""
    for port in range(preferred, preferred + attempts):
        if port_is_free(port, host):
            return port
    # Let the OS pick any free port as a last resort.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((host, 0))
        return sock.getsockname()[1]


if __name__ == "__main__":
    kill_previous_instances()
    port = int(os.environ.get("PORT") or 5000)
    free_port(port)          # kill whatever holds the preferred port
    wait_port_free(port)     # give the OS a moment to release it
    if not port_is_free(port):
        port = find_free_port(port)
    print(f" * Abriendo en http://127.0.0.1:{port}")
    # Reloader off so the auto-selected port is not re-resolved on restart.
    app.run(debug=True, port=port, use_reloader=False)
