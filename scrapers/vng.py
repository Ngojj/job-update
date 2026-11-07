"""VNG (Zalo, ZaloPay, VNGGames, GreenNode...) — trang career.vng.com.vn (Next.js).

Dữ liệu job nằm trong thẻ __NEXT_DATA__ của HTML, mỗi trang 10 job.
"""
import json
import re

from .common import get

BASE = "https://career.vng.com.vn"
LIST_URL = BASE + "/vi/tim-kiem-viec-lam"
NEXT_DATA_RE = re.compile(r'__NEXT_DATA__[^>]*>(.*?)</script>', re.S)


def fetch(cfg: dict) -> list[dict]:
    jobs = []
    page, pages = 1, 1
    max_pages = cfg.get("max_pages", 20)
    while page <= min(pages, max_pages):
        html = get(LIST_URL, params={"page": page}).text
        m = NEXT_DATA_RE.search(html)
        if not m:
            raise RuntimeError("VNG: không tìm thấy __NEXT_DATA__ (trang đổi cấu trúc?)")
        props = json.loads(m.group(1))["props"]["pageProps"]
        pages = int(props.get("pages") or 1)
        for item in props.get("jobs", []):
            slug = item.get("slug", "")
            jobs.append({
                "id": f"vng:{item.get('job_id')}",
                "source": "VNG",
                "title": item.get("title", ""),
                "company": "VNG" + (f" ({item['job_family']})" if item.get("job_family") else ""),
                "url": f"{BASE}/job-search/detail/{slug}",
                "location": item.get("location", ""),
                "salary": "",
                "posted": "",
                # workingType: Official / Collaborator (CTV) — thêm vào để lọc level
                "extra": f"{item.get('workingType', '')} {item.get('job_family', '')}",
            })
        page += 1
    return jobs
