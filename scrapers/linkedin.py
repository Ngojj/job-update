"""LinkedIn — dùng endpoint "jobs-guest" (xem không cần đăng nhập).

Lưu ý: đây là endpoint không chính thức, LinkedIn có thể chặn IP (nhất là IP
của GitHub Actions). Nguồn này được thiết kế "best-effort": lỗi thì bỏ qua,
các nguồn khác vẫn chạy bình thường.

Dùng f_E=1,2 (Internship + Entry level) — LinkedIn tự lọc level nên job từ
nguồn này được đánh dấu level_verified, không cần tiêu đề chứa "fresher/intern".
"""
import re
import time

import requests
from bs4 import BeautifulSoup

from .common import HEADERS, TIMEOUT

API = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
JOB_ID_RE = re.compile(r"-(\d+)/?$")


def fetch(cfg: dict) -> list[dict]:
    jobs = []
    days = cfg.get("posted_within_days", 7)
    for i, query in enumerate(cfg.get("queries", [])):
        if i > 0:
            time.sleep(2)  # lịch sự với LinkedIn, tránh bị rate-limit
        params = {
            "keywords": query,
            "location": cfg.get("location", "Vietnam"),
            "f_E": cfg.get("experience_levels", "1,2"),
            "f_TPR": f"r{days * 86400}",
            "start": 0,
        }
        r = requests.get(API, params=params, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        for card in soup.select("div.base-card"):
            link = card.select_one("a.base-card__full-link, a[href*='/jobs/view/']")
            title = card.select_one("h3")
            if not link or not title:
                continue
            url = link.get("href", "").split("?")[0]
            m = JOB_ID_RE.search(url)
            if not m:
                continue
            # Dùng www.linkedin.com thay vì vn.linkedin.com — subdomain vn.
            # bị một số ISP Việt Nam chặn (ERR_CONNECTION_REFUSED)
            url = f"https://www.linkedin.com/jobs/view/{m.group(1)}"
            company = card.select_one("h4")
            location = card.select_one(".job-search-card__location")
            posted = card.select_one("time[datetime]")
            jobs.append({
                "id": f"linkedin:{m.group(1)}",
                "source": "LinkedIn",
                "title": title.get_text(strip=True),
                "company": company.get_text(strip=True) if company else "",
                "url": url,
                "location": location.get_text(strip=True) if location else "",
                "salary": "",
                "posted": posted.get("datetime", "") if posted else "",
                "extra": "",
                # LinkedIn đã lọc Internship/Entry-level qua f_E → khỏi cần
                # keyword level trong tiêu đề
                "level_verified": True,
            })
    return jobs
