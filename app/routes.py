import os
from flask import Blueprint, jsonify, request, Response
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import time

load_dotenv()

order_bp = Blueprint("orders", __name__)

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "port": os.getenv("DB_PORT")
}

REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency in seconds',
    ['method', 'endpoint']
)


def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)


@order_bp.before_request
def before_request():
    request._start_time = time.time()

@order_bp.after_request
def after_request(response):
    endpoint = request.path
    method = request.method
    status = response.status_code

    REQUEST_COUNT.labels(
        method=method,
        endpoint=endpoint,
        status=status
    ).inc()

    if hasattr(request, '_start_time'):
        REQUEST_LATENCY.labels(
            method=method,
            endpoint=endpoint
        ).observe(time.time() - request._start_time)

    return response

@order_bp.route('/metrics')
def metrics():
    return Response(generate_latest(), mimetype=CONTENT_TYPE_LATEST)


@order_bp.route("/orders", methods=["GET"])
def get_all_orders():
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, product_id, quantity, total_price
            FROM orders
        """)

        orders = cursor.fetchall()
        return jsonify(orders), 200

    except Error as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@order_bp.route("/orders/<int:id>", methods=["GET"])
def get_one_order(id):
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, product_id, quantity, total_price
            FROM orders
            WHERE id = %s
        """, (id,))

        order = cursor.fetchone()

        if not order:
            return jsonify({"error": "Order not found"}), 404

        return jsonify(order), 200

    except Error as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@order_bp.route("/orders", methods=["POST"])
def create_order():
    conn = None
    cursor = None

    try:
        data = request.get_json()

        if not data or "product_id" not in data or "quantity" not in data:
            return jsonify({"error": "product_id and quantity are required"}), 400

        product_id = data["product_id"]
        quantity = data["quantity"]

        if quantity <= 0:
            return jsonify({"error": "quantity must be greater than 0"}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT price FROM products WHERE id = %s",
            (product_id,)
        )

        product = cursor.fetchone()

        if not product:
            return jsonify({"error": "Product not found"}), 404

        price = product["price"]
        total_price = float(price) * int(quantity)

        cursor.execute(
            """
            INSERT INTO orders (product_id, quantity, total_price)
            VALUES (%s, %s, %s)
            """,
            (product_id, quantity, total_price)
        )

        conn.commit()

        order_id = cursor.lastrowid

        return jsonify({
            "id": order_id,
            "product_id": product_id,
            "quantity": quantity,
            "total_price": total_price
        }), 201

    except Error as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()