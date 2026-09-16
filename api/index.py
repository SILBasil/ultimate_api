import os
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


# ดึงค่าการเชื่อมต่อ Database จาก Environment Variables
DB_HOST = (os.getenv("DB_HOST_TIDB") or os.getenv("DB_HOST")).strip("'\"")
DB_PORT = (os.getenv("DB_PORT_TIDB") or os.getenv("DB_PORT")).strip("'\"")
DB_USER = (os.getenv("DB_USERNAME_TIDB") or os.getenv("DB_USER")).strip("'\"")
DB_PASSWORD = (os.getenv("DB_PASSWORD_TIDB") or os.getenv("DB_PASSWORD")).strip("'\"")
DB_NAME = (os.getenv("DB_DATABASE_TIDB") or os.getenv("DB_NAME")).strip("'\"")

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# สร้าง SQLAlchemy Engine พร้อม SSL CA จาก certifi (รองรับทั้ง Linux บน Vercel และ Local)
engine = create_engine(
    DATABASE_URL,
    connect_args={"ssl": {"ca": certifi.where()}},
    pool_recycle=300,
    pool_pre_ping=True,
)


@app.route("/", methods=["GET"])
def root():
    return jsonify(
        {
            "service": "Ultimate Products REST API",
            "status": "online",
            "endpoints": {
                "health": "/api/health",
                "cron_keep_active": "/api/cron",
                "products_list": "/api/products?limit=20&offset=0",
                "product_detail": "/api/products/<order_id>",
                "summary": "/api/summary",
            },
        }
    )


@app.route("/api/health", methods=["GET"])
def health():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return jsonify({"status": "healthy", "database": "connected"}), 200
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500


@app.route("/api/cron", methods=["GET"])
def cron_keep_active():
    """เส้น API สำหรับ Cron Job ยิงเพื่อรักษาความ Active ป้องกันระบบ Pause"""
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
def get_products():
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

    try:
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
def get_product_by_id(order_id):
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
def get_summary():
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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
