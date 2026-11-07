"""LinkedIn — dùng endpoint "jobs-guest" (xem không cần đăng nhập).

Lưu ý: đây là endpoint không chính thức, LinkedIn có thể chặn IP (nhất là IP
của GitHub Actions). Nguồn này được thiết kế "best-effort": lỗi thì bỏ qua,
các nguồn khác vẫn chạy bình thường.

Dùng f_E=1,2 (Internship + Entry level) — LinkedIn tự lọc level nên job từ
nguồn này được đánh dấu level_verified, không cần tiêu đề chứa "fresher/intern".
"""
import re
import time

from bs4 import BeautifulSoup

from .common import get

API = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
JOB_ID_RE = re.compile(r"-(\d+)/?$")


def _parse_cards(html: str) -> list[dict]:
    jobs = []
    soup = BeautifulSoup(html, "html.parser")
    for card in soup.select("div.base-card"):
        link = card.select_one("a.base-card__full-link, a[href*='/jobs/view/']")
        title = card.select_one("h3")
        if not link or not title:
            continue
        m = JOB_ID_RE.search(link.get("href", "").split("?")[0])
        if not m:
            continue
        company = card.select_one("h4")
        location = card.select_one(".job-search-card__location")
        posted = card.select_one("time[datetime]")
        jobs.append({
            "id": f"linkedin:{m.group(1)}",
            "source": "LinkedIn",
            "title": title.get_text(strip=True),
            "company": company.get_text(strip=True) if company else "",
            # Dùng www.linkedin.com thay vì vn.linkedin.com — subdomain vn.
            # bị một số ISP Việt Nam chặn (ERR_CONNECTION_REFUSED)
            "url": f"https://www.linkedin.com/jobs/view/{m.group(1)}",
            "location": location.get_text(strip=True) if location else "",
            "salary": "",
            "posted": posted.get("datetime", "") if posted else "",
            "extra": "",
            # LinkedIn đã lọc Internship/Entry-level qua f_E → khỏi cần
            # keyword level trong tiêu đề
            "level_verified": True,
        })
    return jobs


def fetch(cfg: dict) -> list[dict]:
    jobs = []
    days = cfg.get("posted_within_days", 7)
    max_pages = cfg.get("max_pages", 4)  # mỗi trang ~10 job
    for query in cfg.get("queries", []):
        for page in range(max_pages):
            time.sleep(2)  # lịch sự với LinkedIn, tránh bị rate-limit
            params = {
                "keywords": query,
                "location": cfg.get("location", "Vietnam"),
                "f_E": cfg.get("experience_levels", "1,2"),
                "f_TPR": f"r{days * 86400}",
                "start": page * 10,
            }
            try:
                html = get(API, params=params, retries=2).text
            except Exception:
                if not jobs:
                    raise  # bị chặn ngay từ đầu → báo lỗi nguồn
                break  # lỗi ở giữa chừng thì giữ phần đã lấy được
            cards = _parse_cards(html)
            if not cards:
                break
            jobs.extend(cards)
    return jobs
