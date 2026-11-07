"""TopCV — parse HTML trang tìm kiếm.

Lưu ý: TopCV hay chặn IP datacenter bằng Cloudflare (403) → nguồn này là
"best-effort": chạy được trên máy nhà, có thể lỗi trên GitHub Actions.
"""
import re

from bs4 import BeautifulSoup

import time

from .common import get, slugify

# l2 = Hồ Chí Minh
URL = "https://www.topcv.vn/tim-viec-lam-{slug}-tai-ho-chi-minh-l2"
JOB_ID_RE = re.compile(r"/(\d+)\.html")


def fetch(cfg: dict) -> list[dict]:
    jobs = []
    max_pages = cfg.get("max_pages", 5)
    for query in cfg.get("queries", []):
        slug = slugify(query)
        seen = set()
        for page in range(1, max_pages + 1):
            time.sleep(1.5)  # chậm lại để Cloudflare ít chặn hơn
            try:
                html = get(URL.format(slug=slug), params={"page": page}, retries=1).text
            except Exception:
                if not jobs:
                    raise  # bị chặn ngay từ đầu → báo lỗi nguồn
                break  # đã có dữ liệu thì giữ lại, bỏ qua query bị chặn
            soup = BeautifulSoup(html, "html.parser")
            cards = soup.select("div.job-item-search-result")
            fresh = 0
            for card in cards:
                job_id = card.get("data-job-id")
                link = card.select_one("h3.title a")
                if not job_id or not link or job_id in seen:
                    continue
                seen.add(job_id)
                fresh += 1
                company = card.select_one(".company-name")
                city = card.select_one(".city-text, .address")
                salary = card.select_one(".title-salary")
                updated = card.select_one(".label-update")
                jobs.append({
                    "id": f"topcv:{job_id}",
                    "source": "TopCV",
                    "title": link.get_text(strip=True),
                    "company": company.get_text(strip=True) if company else "",
                    "url": link.get("href", "").split("?")[0],
                    "location": city.get_text(strip=True) if city else "",
                    "salary": salary.get_text(strip=True) if salary else "",
                    "posted": updated.get_text(strip=True) if updated else "",
                    "extra": "",
                })
            if fresh == 0:
                break
    return jobs
