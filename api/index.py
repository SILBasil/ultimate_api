import os
import urllib.parse
from functools import wraps
from flask import Flask, request, jsonify, make_response

try:
    from flask_cors import CORS

    has_cors = True
except ImportError:
    has_cors = False

import certifi
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
if has_cors:
    CORS(app)


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    return response


# Helper to get environment variables safely
def get_env_safe(keys, default=""):
    for k in keys:
        val = os.getenv(k)
        if val is not None and str(val).strip() != "":
            return str(val).strip("'\"")
    return default


DB_HOST = get_env_safe(["DB_HOST_TIDB", "DB_HOST"])
DB_PORT = get_env_safe(["DB_PORT_TIDB", "DB_PORT"], "4000")
DB_USER = get_env_safe(["DB_USERNAME_TIDB", "DB_USER"])
DB_PASSWORD = get_env_safe(["DB_PASSWORD_TIDB", "DB_PASSWORD"])
DB_NAME = get_env_safe(["DB_DATABASE_TIDB", "DB_NAME"])

# Bearer Token Authentication
API_BEARER_TOKEN = get_env_safe(["API_BEARER_TOKEN", "BEARER_TOKEN", "AUTH_TOKEN"])

# SQLAlchemy Engine with SSL CA
if DB_HOST and DB_USER and DB_PASSWORD and DB_NAME:
    escaped_password = urllib.parse.quote_plus(DB_PASSWORD)
    DATABASE_URL = (
        f"mysql+pymysql://{DB_USER}:{escaped_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    try:
        engine = create_engine(
            DATABASE_URL,
            connect_args={"ssl": {"ca": certifi.where()}},
            pool_recycle=300,
            pool_pre_ping=True,
        )
    except Exception as err:
        engine = None
        engine_init_error = str(err)
    else:
        engine_init_error = None
else:
    engine = None
    engine_init_error = (
        "Database credentials are not configured in environment variables."
    )


# ==============================================================================
# Decorator for Bearer Token Authentication
# ==============================================================================
def require_bearer_token(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not API_BEARER_TOKEN:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Server authorization token is not configured.",
                    }
                ),
                500,
            )

        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Missing Authorization header. Expected format: 'Authorization: Bearer <TOKEN>'",
                    }
                ),
                401,
            )

        parts = auth_header.split(" ")
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Invalid Authorization header format. Expected 'Bearer <TOKEN>'",
                    }
                ),
                401,
            )

        token = parts[1]
        if token != API_BEARER_TOKEN:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Invalid or unauthorized Bearer Token",
                    }
                ),
                403,
            )

        return f(*args, **kwargs)

    return decorated_function


# ==============================================================================
# Endpoints
# ==============================================================================


@app.route("/", methods=["GET"])
def root():
    return jsonify(
        {
            "service": "Enterprise Retail & Products REST API",
            "status": "online",
            "auth_type": "Bearer Token",
            "endpoints": {
                "public_health": "/api/health",
                "cron_keep_active": "/api/cron",
                "protected_products_list": "/api/products?limit=20&offset=0",
                "protected_product_detail": "/api/products/<order_id>",
                "protected_summary": "/api/summary",
                "branch_01_sales": "/api/v1/branches/1/sales?page=1&limit=50",
                "branch_02_sales": "/api/v1/branches/2/sales?page=1&limit=50",
            },
        }
    )


@app.route("/api/health", methods=["GET"])
def health():
    if engine is None:
        return jsonify({"status": "unhealthy", "error": engine_init_error}), 500
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return jsonify({"status": "healthy", "database": "connected"}), 200
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500


@app.route("/api/cron", methods=["GET"])
def cron_keep_active():
    if engine is None:
        return jsonify({"status": "error", "error": engine_init_error}), 500
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM products")).scalar()
        return (
            jsonify(
                {
                    "status": "active",
                    "message": "Keep-alive ping successful",
                    "total_products_in_db": result,
                }
            ),
            200,
        )
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500


@app.route("/api/products", methods=["GET"])
@require_bearer_token
def get_products():
    if engine is None:
        return jsonify({"status": "error", "message": engine_init_error}), 500
    try:
        limit = min(int(request.args.get("limit", 20)), 100)
        offset = int(request.args.get("offset", 0))
        status = request.args.get("status")
        item_name = request.args.get("item_name")

        where_clauses = []
        params = {"limit": limit, "offset": offset}

        if status:
            where_clauses.append("status = :status")
            params["status"] = status
        if item_name:
            where_clauses.append("item_name LIKE :item_name")
            params["item_name"] = f"%{item_name}%"

        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

        query = f"""
            SELECT order_id, customer_id, item_name, quantity, unit_price_thb, status, order_date
            FROM products
            {where_sql}
            ORDER BY order_id ASC
            LIMIT :limit OFFSET :offset
        """

        count_query = f"SELECT COUNT(*) FROM products {where_sql}"

        with engine.connect() as conn:
            total_filtered = conn.execute(text(count_query), params).scalar()
            result = conn.execute(text(query), params)
            products = [dict(row._mapping) for row in result.fetchall()]

        return (
            jsonify(
                {
                    "status": "success",
                    "total": total_filtered,
                    "limit": limit,
                    "offset": offset,
                    "data": products,
                }
            ),
            200,
        )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/products/<order_id>", methods=["GET"])
@require_bearer_token
def get_product_by_id(order_id):
    if engine is None:
        return jsonify({"status": "error", "message": engine_init_error}), 500
    try:
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT * FROM products WHERE order_id = :order_id"),
                {"order_id": order_id},
            ).fetchone()

            if not result:
                return (
                    jsonify(
                        {"status": "error", "message": "Product / Order not found"}
                    ),
                    404,
                )

            return jsonify({"status": "success", "data": dict(result._mapping)}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/summary", methods=["GET"])
@require_bearer_token
def get_summary():
    if engine is None:
        return jsonify({"status": "error", "message": engine_init_error}), 500
    try:
        with engine.connect() as conn:
            total_count = conn.execute(text("SELECT COUNT(*) FROM products")).scalar()
            status_dist = conn.execute(
                text("SELECT status, COUNT(*) as count FROM products GROUP BY status")
            ).fetchall()

        return (
            jsonify(
                {
                    "status": "success",
                    "total_records": total_count,
                    "status_distribution": {row[0]: row[1] for row in status_dist},
                }
            ),
            200,
        )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ==============================================================================
# RESTful Branch Sales Endpoints (Standard RESTful Resource Naming)
# Format: /api/v1/branches/{branch_id}/sales
# รองรับ Pagination (page, limit) โดยไม่ใส่ total_pages
# ==============================================================================


@app.route("/api/v1/branches/1/sales", methods=["GET"])
@require_bearer_token
def get_branch_01_sales():
    if engine is None:
        return jsonify({"status": "error", "message": engine_init_error}), 500
    try:
        page = max(int(request.args.get("page", 1)), 1)
        limit = min(max(int(request.args.get("limit", 50)), 1), 200)
        offset = (page - 1) * limit

        query = text(
            """
            SELECT transaction_date, branch_id, branch_name, product_id,
                   product_name, category, CAST(unit_price AS FLOAT) AS unit_price,
                   quantity_sold, CAST(total_amount AS FLOAT) AS total_amount,
                   CAST(profit AS FLOAT) AS profit
            FROM branch_01_sales
            ORDER BY id ASC
            LIMIT :limit OFFSET :offset
            """
        )

        with engine.connect() as conn:
            result = conn.execute(query, {"limit": limit, "offset": offset})
            rows = [dict(row._mapping) for row in result.fetchall()]

        return (
            jsonify(
                {
                    "status": "success",
                    "branch_id": "BR-001",
                    "branch_name": "สาขาสยามพารากอน",
                    "page": page,
                    "limit": limit,
                    "data": rows,
                }
            ),
            200,
        )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/v1/branches/2/sales", methods=["GET"])
@require_bearer_token
def get_branch_02_sales():
    if engine is None:
        return jsonify({"status": "error", "message": engine_init_error}), 500
    try:
        page = max(int(request.args.get("page", 1)), 1)
        limit = min(max(int(request.args.get("limit", 50)), 1), 200)
        offset = (page - 1) * limit

        query = text(
            """
            SELECT transaction_date, branch_id, branch_name, product_id,
                   product_name, category, CAST(unit_price AS FLOAT) AS unit_price,
                   quantity_sold, CAST(total_amount AS FLOAT) AS total_amount,
                   CAST(profit AS FLOAT) AS profit
            FROM branch_02_sales
            ORDER BY id ASC
            LIMIT :limit OFFSET :offset
            """
        )

        with engine.connect() as conn:
            result = conn.execute(query, {"limit": limit, "offset": offset})
            rows = [dict(row._mapping) for row in result.fetchall()]

        return (
            jsonify(
                {
                    "status": "success",
                    "branch_id": "BR-002",
                    "branch_name": "สาขาเซ็นทรัลเวิลด์",
                    "page": page,
                    "limit": limit,
                    "data": rows,
                }
            ),
            200,
        )
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
