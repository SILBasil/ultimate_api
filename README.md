# Ultimate Products & Retail REST API (Flask on Vercel)

REST API สำหรับดึงข้อมูลและจัดการข้อมูลสินค้า/คำสั่งซื้อ และยอดขายสาขา เชื่อมต่อกับ TiDB Cloud และ Deploy อยู่บน Vercel Serverless

- **Base URL:** `https://ultimate-api-alpha.vercel.app`

---

## 🔐 การยืนยันตัวตน (Authentication)
สำหรับ Protected Endpoints จะต้องส่ง **Bearer Token** แนบไปใน HTTP Header:

```http
Authorization: Bearer <API_BEARER_TOKEN>
```

---

## 🚀 รายการ Endpoints ทั้งหมด

### 1. Public Endpoints (ไม่ต้องใช้ Token)

| Endpoint | Method | รายละเอียด | ตัวอย่าง URL |
| :--- | :---: | :--- | :--- |
| `/` | `GET` | ตรวจสอบข้อมูล API และสถานะเบื้องต้น | [`https://ultimate-api-alpha.vercel.app/`](https://ultimate-api-alpha.vercel.app/) |
| `/api/health` | `GET` | ตรวจสอบสุขภาพของ API และสถานะเชื่อมต่อ Database | [`https://ultimate-api-alpha.vercel.app/api/health`](https://ultimate-api-alpha.vercel.app/api/health) |
| `/api/cron` | `GET` | เส้น Ping สำหรับ Vercel Cron Job (Keep-alive) | [`https://ultimate-api-alpha.vercel.app/api/cron`](https://ultimate-api-alpha.vercel.app/api/cron) |

---

### 2. Branch Sales Endpoints (Exam / Data Integration) 🏬

สำหรับดึงข้อมูลยอดขายประจำสาขา โดยใช้ระบบ **Pagination (`page`, `limit`)** ที่ไม่มี `total_pages` ส่งกลับมา เพื่อให้ Client วน Loop ดึงจนกว่า `data` จะเป็น Array ว่าง `[]`

#### 🛍️ สาขา 01 - สยามพารากอน
- **URL:** `https://ultimate-api-alpha.vercel.app/api/v1/branches/1/sales`
- **Method:** `GET`
- **Headers:** `Authorization: Bearer <API_BEARER_TOKEN>`
- **Query Parameters:**
  - `page` *(optional)*: เลขหน้าที่ต้องการดึง (default: `1`)
  - `limit` *(optional)*: จำนวนแถวต่อหน้า (default: `50`, min: `1`, max: `200`)
- **ตัวอย่าง URL:**
  - `https://ultimate-api-alpha.vercel.app/api/v1/branches/1/sales?page=1&limit=50`

#### 🛍️ สาขา 02 - เซ็นทรัลเวิลด์
- **URL:** `https://ultimate-api-alpha.vercel.app/api/v1/branches/2/sales`
- **Method:** `GET`
- **Headers:** `Authorization: Bearer <API_BEARER_TOKEN>`
- **Query Parameters:**
  - `page` *(optional)*: เลขหน้าที่ต้องการดึง (default: `1`)
  - `limit` *(optional)*: จำนวนแถวต่อหน้า (default: `50`, min: `1`, max: `200`)
- **ตัวอย่าง URL:**
  - `https://ultimate-api-alpha.vercel.app/api/v1/branches/2/sales?page=1&limit=50`

#### 📋 ตัวอย่าง Response Data (`GET /api/v1/branches/1/sales`)
```json
{
  "status": "success",
  "branch_id": "BR-001",
  "branch_name": "สาขาสยามพารากอน",
  "page": 1,
  "limit": 50,
  "data": [
    {
      "branch_id": "BR-001",
      "branch_name": "สาขาสยามพารากอน",
      "category": "เครื่องดื่ม",
      "product_id": "PROD-001",
      "product_name": "ชาเขียวมัทฉะพรีเมียม",
      "profit": 1560.0,
      "quantity_sold": 52,
      "total_amount": 3380.0,
      "transaction_date": "2026-09-01",
      "unit_price": 65.0
    }
  ]
}
```

---

### 3. Products Endpoints (Protected) 📦

#### 📦 ดึงรายการสินค้าทั้งหมด (Pagination & Filter)
- **URL:** `https://ultimate-api-alpha.vercel.app/api/products`
- **Method:** `GET`
- **Query Parameters:**
  - `limit` *(optional)*: จำนวนข้อมูลต่อหน้า (default: `20`, max: `100`)
  - `offset` *(optional)*: ตำแหน่งเริ่มต้น (default: `0`)
  - `status` *(optional)*: กรองตามสถานะ เช่น `Completed`, `Pending`, `Cancelled`
  - `item_name` *(optional)*: ค้นหาตามชื่อสินค้าบางส่วน
- **ตัวอย่าง URL:**
  - `https://ultimate-api-alpha.vercel.app/api/products?limit=10&offset=0`
  - `https://ultimate-api-alpha.vercel.app/api/products?status=Completed&item_name=Wireless`

#### 🔍 ดึงรายละเอียดสินค้าตาม Order ID
- **URL:** `https://ultimate-api-alpha.vercel.app/api/products/<order_id>`
- **Method:** `GET`
- **ตัวอย่าง URL:** `https://ultimate-api-alpha.vercel.app/api/products/ORD-2026-000001`

#### 📊 สรุปยอดและสถิติข้อมูล
- **URL:** `https://ultimate-api-alpha.vercel.app/api/summary`
- **Method:** `GET`

---

## 💻 ตัวอย่างการดึงข้อมูล Branch Sales (Python Pagination Loop)

ตัวอย่างสคริปต์ Python สำหรับวนลูปดึงข้อมูลยอดขายสาขาจนครบทุกหน้า:

```python
import requests
import pandas as pd

API_TOKEN = "a2b6247fb1a5434a4376457f1097dd1caae6315304494e3fe76a7358f1bac441"
headers = {"Authorization": f"Bearer {API_TOKEN}"}

def fetch_branch_sales(branch_number):
    url = f"https://ultimate-api-alpha.vercel.app/api/v1/branches/{branch_number}/sales"
    page = 1
    limit = 100
    all_data = []

    while True:
        res = requests.get(url, headers=headers, params={"page": page, "limit": limit})
        res.raise_for_status()
        records = res.json().get("data", [])
        
        if not records:
            break
            
        all_data.extend(records)
        print(f"Branch {branch_number}: Fetched page {page}, got {len(records)} records")
        page += 1

    return pd.DataFrame(all_data)

# ทดสอบดึงข้อมูลสาขา 1 และ 2
df_branch_01 = fetch_branch_sales(1)
df_branch_02 = fetch_branch_sales(2)
print(f"Branch 01 Total Rows: {len(df_branch_01)}")
print(f"Branch 02 Total Rows: {len(df_branch_02)}")
```

---

## 📬 Postman Collection
สามารถนำไฟล์ `postman_collection.json` ไปกด **Import** ใน Postman เพื่อทดสอบ API ทั้งหมดได้ทันที
- **Variables ใน Collection:**
  - `base_url`: `https://ultimate-api-alpha.vercel.app`
  - `bearer_token`: Token สำหรับทดสอบ

---

## 🛠️ การรันในเครื่อง (Local Development)
1. ติดตั้ง Dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. คัดลอกและตั้งค่า `.env`:
   ```bash
   cp .env.example .env
   ```
3. รัน Server:
   ```bash
   python api/index.py
   ```
   API จะทำงานที่ `http://localhost:5000`
