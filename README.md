# 💼 Job Alert Bot — Báo việc Intern/Fresher về Telegram

Tự động quét **VietnamWorks, ITviec, TopDev** mỗi 2 tiếng, lọc các vị trí
**Intern / Fresher** ngành **Software / Data / AI**, và gửi job **mới** về Telegram.
Chạy miễn phí trên GitHub Actions — không cần bật máy tính.

## Kiến trúc

```
GitHub Actions (cron 2h/lần)
  └─ main.py
      ├─ scrapers/   → lấy job từ VietnamWorks (API), TopDev (API), ITviec (HTML)
      ├─ filters.py  → lọc level (intern/fresher) + ngành (software/data/AI) + địa điểm
      ├─ storage.py  → data/seen_jobs.json: nhớ job đã gửi, không báo trùng
      └─ notifier.py → gửi tin nhắn Telegram (gom nhiều job / 1 tin)
```

## Setup lần đầu (~10 phút)

### Bước 1 — Lấy `chat_id` Telegram

Bạn đã có bot token từ @BotFather. Giờ lấy chat_id:

1. Mở Telegram, **nhắn 1 tin bất kỳ cho bot của bạn** (ví dụ "hi")
2. Mở trình duyệt: `https://api.telegram.org/bot<TOKEN_CỦA_BẠN>/getUpdates`
3. Tìm `"chat":{"id":123456789` → số đó là `chat_id`

### Bước 2 — Chạy thử trên máy

```powershell
pip install -r requirements.txt
python main.py --dry-run          # chỉ in ra màn hình, không gửi

# Gửi thật về Telegram:
$env:TELEGRAM_BOT_TOKEN = "123456:ABC-xyz..."
$env:TELEGRAM_CHAT_ID   = "123456789"
python main.py
```

### Bước 3 — Đưa lên GitHub Actions (chạy tự động)

1. Tạo repo mới trên GitHub (nên để **Private**)
2. Push code:
   ```powershell
   git init
   git add .
   git commit -m "Job alert bot"
   git branch -M main
   git remote add origin https://github.com/<username>/<repo>.git
   git push -u origin main
   ```
3. Trên GitHub: **Settings → Secrets and variables → Actions → New repository secret**, tạo 2 secret:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
4. Vào tab **Actions** → chọn workflow **Job Alert** → **Run workflow** để chạy thử ngay.

Sau đó bot tự chạy mỗi 2 tiếng. File `data/seen_jobs.json` được commit lại sau mỗi lần
chạy để không báo trùng.

> ⚠️ GitHub tự tắt cron nếu repo không có commit nào trong 60 ngày — bot vẫn tự commit
> `seen_jobs.json` thường xuyên nên không lo, nhưng nếu thấy im lặng lâu hãy vào tab
> Actions kiểm tra.

## Tuỳ chỉnh

Mọi thứ nằm trong [config.yaml](config.yaml):

- `level_keywords` / `field_keywords` / `exclude_keywords` — thêm bớt từ khoá lọc
- `locations: ["Hồ Chí Minh", "Remote"]` — chỉ nhận job ở nơi bạn muốn (để `[]` = mọi nơi)
- `sources.<tên>.enabled: false` — tắt một nguồn
- `max_new_per_run` — số job tối đa mỗi lần gửi
- Đổi tần suất quét: sửa `cron` trong [.github/workflows/job-alert.yml](.github/workflows/job-alert.yml)

## Ghi chú về LinkedIn / TopCV

- **LinkedIn**: dùng endpoint "jobs-guest" (xem không cần đăng nhập) với filter chính chủ
  `f_E=1,2` (Internship + Entry level). Đây là endpoint **không chính thức** — không cần
  tài khoản nên không có rủi ro khoá account, nhưng LinkedIn có thể chặn IP (nhất là IP
  GitHub Actions, lỗi 429/999). Nguồn này lỗi thì các nguồn khác vẫn chạy bình thường.
  Nếu bị chặn thường xuyên trên Actions, đặt `sources.linkedin.enabled: false` và bật
  **LinkedIn Job Alerts qua email** thay thế.
- **TopCV**: chặn bot bằng Cloudflare (HTTP 403) — cần headless browser, sẽ thêm ở phase sau.

## Ghi chú kỹ thuật

- VietnamWorks & TopDev: gọi API JSON nội bộ mà chính website của họ dùng → ổn định hơn parse HTML.
- ITviec: parse HTML trang `/it-jobs/fresher` và `/it-jobs/intern` (selector: `h3[data-url]`).
- Job "đã gửi" được nhớ 60 ngày rồi tự xoá (`seen_retention_days`).
- Một nguồn lỗi không làm sập cả pipeline — các nguồn còn lại vẫn chạy bình thường.
"# job-update" 
