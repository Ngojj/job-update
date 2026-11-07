# 💼 Job Alert Bot — Báo việc Intern/Fresher về Telegram

Tự động quét **job board** (VietnamWorks, TopDev, ITviec, LinkedIn, TopCV, CareerViet, Glints)
và **trang tuyển dụng trực tiếp của công ty** (VNG/Zalo, Bosch, Grab, Intel, Nvidia, Cisco, Visa,
Mastercard, Amazon...), lọc các vị trí **Intern / Fresher** ngành **Software / Data / AI** ở HCM
và gửi về Telegram.
Chạy miễn phí trên GitHub Actions — không cần bật máy tính.

## Kiến trúc

```
GitHub Actions (cron 2h/lần)
  └─ main.py
      ├─ scrapers/   → job board (API/HTML) + trang tuyển dụng công ty (ATS công khai)
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

## Nguồn dữ liệu

| Nhóm | Nguồn | Cách lấy | Phạm vi |
|---|---|---|---|
| Job board | VietnamWorks | API nội bộ, lọc `jobLevelId` 1 (Fresher) + 8 (Intern) + HCM | **toàn bộ** job thuộc level đó |
| Job board | TopDev | API nội bộ, lọc `job_levels_ids` Thực tập + Mới tốt nghiệp + HCM | **toàn bộ** |
| Job board | ITviec | HTML `/it-jobs/fresher`, `/it-jobs/intern`, có phân trang | toàn bộ 2 trang level |
| Job board | LinkedIn | guest endpoint, `f_E=1,2`, nhiều query | best-effort (có thể bị chặn) |
| Job board | TopCV, CareerViet, Glints | HTML / `__NEXT_DATA__`, theo từ khoá | theo từ khoá |
| Công ty | VNG, Zalo, ZaloPay, VNGGames | `career.vng.com.vn` (`__NEXT_DATA__`) | toàn bộ job đang mở |
| Công ty | Bosch, Grab | SmartRecruiters API công khai | toàn bộ job ở VN |
| Công ty | Intel, Nvidia, Marvell, Cisco, Mastercard, Visa, Accenture, PwC, Salesforce, Medtronic, Manulife, Citi, KLA, LSEG | Workday API công khai | toàn bộ job ở VN |
| Công ty | Amazon / AWS | `amazon.jobs/search.json` | toàn bộ job ở VN |

### Thêm công ty mới
- Công ty dùng **SmartRecruiters** (URL dạng `jobs.smartrecruiters.com/<Tên>`): thêm `{id: <Tên>, name: ...}` vào `sources.smartrecruiters.companies`.
- Công ty dùng **Workday** (URL dạng `<host>.myworkdayjobs.com/<site>`): thêm `{name, host, tenant, site}` vào `sources.workday.companies`.
- Công ty dùng trang riêng (FPT, Viettel, MoMo, Shopee, Tiki...): chưa có API công khai → tạm thời job của họ vẫn xuất hiện qua VietnamWorks/TopDev/ITviec/LinkedIn.

## Ghi chú về LinkedIn / TopCV

- **LinkedIn**: dùng endpoint "jobs-guest" (xem không cần đăng nhập) với filter chính chủ
  `f_E=1,2` (Internship + Entry level). Đây là endpoint **không chính thức** — không cần
  tài khoản nên không có rủi ro khoá account, nhưng LinkedIn có thể chặn IP (nhất là IP
  GitHub Actions, lỗi 429/999). Nguồn này lỗi thì các nguồn khác vẫn chạy bình thường.
  Nếu bị chặn thường xuyên trên Actions, đặt `sources.linkedin.enabled: false` và bật
  **LinkedIn Job Alerts qua email** thay thế.
- **TopCV**: chặn bot bằng Cloudflare — chạy được trên máy nhà nhưng hay bị 403 trên IP GitHub
  Actions. Nguồn này lỗi thì bỏ qua; tin Telegram sẽ ghi rõ "⚠️ Không quét được: topcv".

## Ghi chú kỹ thuật

- VietnamWorks & TopDev: gọi API JSON nội bộ mà chính website của họ dùng → ổn định hơn parse HTML.
  TopDev dùng tham số `keyword` (số ít) — `keywords` bị API bỏ qua; mỗi job nhiều chi nhánh được đếm
  nhiều dòng nên `total` lớn hơn số job thật.
- ITviec: parse HTML trang `/it-jobs/fresher` và `/it-jobs/intern` (selector: `h3[data-url]`).
- Nguồn nào trả 0 job hoặc lỗi sẽ được cảnh báo ngay trong tin Telegram (danh sách có thể chưa đầy đủ).
- Job "đã gửi" được nhớ 60 ngày rồi tự xoá (`seen_retention_days`).
- Một nguồn lỗi không làm sập cả pipeline — các nguồn còn lại vẫn chạy bình thường.
"# job-update" 
