# Ultimate Products REST API (Flask on Vercel)

REST API สำหรับดึงข้อมูลและจัดการข้อมูลสินค้า/คำสั่งซื้อ เชื่อมต่อกับ TiDB Cloud และ Deploy อยู่บน Vercel Serverless

- **Base URL:** `https://ultimate-api-alpha.vercel.app`

---

## 🔐 การยืนยันตัวตน (Authentication)
สำหรับ Protected Endpoints จะต้องส่ง **Bearer Token** แนบไปใน HTTP Header:

```http
Authorization: Bearer <API_BEARER_TOKEN>
```

---

## 🚀 รายการ Endpoints

### 1. Public Endpoints (ไม่ต้องใช้ Token)

| Endpoint | Method | รายละเอียด | ตัวอย่าง URL |
| :--- | :---: | :--- | :--- |
| `/` | `GET` | ตรวจสอบข้อมูล API และสถานะเบื้องต้น | [`https://ultimate-api-alpha.vercel.app/`](https://ultimate-api-alpha.vercel.app/) |
| `/api/health` | `GET` | ตรวจสอบสุขภาพของ API และสถานะเชื่อมต่อ Database | [`https://ultimate-api-alpha.vercel.app/api/health`](https://ultimate-api-alpha.vercel.app/api/health) |
| `/api/cron` | `GET` | เส้น Ping สำหรับ Vercel Cron Job (Keep-alive) | [`https://ultimate-api-alpha.vercel.app/api/cron`](https://ultimate-api-alpha.vercel.app/api/cron) |

---

### 2. Protected Endpoints (ต้องใช้ Bearer Token)

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
- **ตัวอย่าง URL:** `https://ultimate-api-alpha.vercel.app/api/products/ORD-000001`

#### 📊 สรุปยอดและสถิติข้อมูล
- **URL:** `https://ultimate-api-alpha.vercel.app/api/summary`
- **Method:** `GET`
- **คำอธิบาย:** คืนค่าจำนวน Records ทั้งหมดและสัดส่วนของแต่ละ Status

---

## 💻 ตัวอย่างการเรียกใช้งาน (Code Examples)

### cURL
```bash
# Health Check (Public)
curl https://ultimate-api-alpha.vercel.app/api/health

# Get Products (Protected)
curl -H "Authorization: Bearer <API_BEARER_TOKEN>" \
  "https://ultimate-api-alpha.vercel.app/api/products?limit=20&offset=0"
```

### JavaScript (Fetch)
```javascript
const response = await fetch("https://ultimate-api-alpha.vercel.app/api/products?limit=20", {
  method: "GET",
  headers: {
    "Authorization": "Bearer <API_BEARER_TOKEN>"
  }
});
const data = await response.json();
console.log(data);
```

### Python (Requests)
```python
import requests

headers = {
    "Authorization": "Bearer <API_BEARER_TOKEN>"
}
response = requests.get(
    "https://ultimate-api-alpha.vercel.app/api/products",
    headers=headers,
    params={"limit": 20, "offset": 0}
)
print(response.json())
```

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
