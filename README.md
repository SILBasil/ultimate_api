# Ultimate Products REST API (Flask on Vercel)

REST API สำหรับดึงข้อมูลสินค้า/คำสั่งซื้อจาก TiDB Cloud Deploy บน Vercel Serverless

## 🚀 Endpoints
- `GET /` : ข้อมูล API เบื้องต้น
- `GET /api/health` : เช็คสถานะการเชื่อมต่อ Database
- `GET /api/products` : ดึงรายการสินค้า (รองรับ `limit`, `offset`, `status`, `item_name`)
- `GET /api/products/<order_id>` : ดึงรายละเอียดสินค้าตาม order_id
- `GET /api/summary` : สรุปยอดและสถิติสินค้า
- `GET /api/cron` : เส้น Ping สำหรับ Cron Job ป้องกันระบบ Sleep/Pause

## ⚙️ Environment Variables (ตั้งค่าใน Vercel)
- `DB_HOST` = gateway01.ap-southeast-1.prod.aws.tidbcloud.com
- `DB_PORT` = 4000
- `DB_USER` = 2d9jdrvr2SNSUNq.reader_user
- `DB_PASSWORD` = StrongPassword123!
- `DB_NAME` = db_ultimate
