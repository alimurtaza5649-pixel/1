from flask import Flask, jsonify, request
import sqlite3
import hashlib
import os


app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "products.db")


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def create_table():
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


@app.route("/init", methods=["GET"])
def init_db():
    create_table()
    return jsonify({"message": "Table ready"})


@app.route("/")
def home():
    return jsonify({"message": "Hello from our first Flask Server!"})


@app.route("/products", methods=["GET"])
def get_products():
    conn = get_db_connection()
    rows = conn.execute("SELECT * FROM products").fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])


@app.route("/products", methods=["POST"])
def add_product():
    data = request.get_json(silent=True)

    if not data or not data.get("name") or not isinstance(data.get("price"), (int, float)):
        return jsonify({"error": "name (text) and price (number) are required"}), 400

    conn = get_db_connection()
    cursor = conn.execute(
        "INSERT INTO products (name, price) VALUES (?, ?)",
        (data["name"], data["price"]),
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()

    new_product = {"id": new_id, "name": data["name"], "price": data["price"]}
    return jsonify({"message": "Product added", "product": new_product}), 201


@app.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "JSON body is required"}), 400

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400

    hashed_password = hash_password(password)

    conn = get_db_connection()
    try:
        conn.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (username, hashed_password),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        return jsonify({"error": "Username already exists"}), 400
    finally:
        conn.close()

    return jsonify({"message": "User registered successfully"}), 201


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "JSON body is required"}), 400

    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400

    hashed_password = hash_password(password)

    conn = get_db_connection()
    user = conn.execute(
        "SELECT * FROM users WHERE username = ? AND password = ?",
        (username, hashed_password),
    ).fetchone()
    conn.close()

    if user:
        return jsonify({"message": f"Welcome {username}!"})
    return jsonify({"error": "Invalid credentials"}), 401


if __name__ == "__main__":
    create_table()
    app.run(debug=True)