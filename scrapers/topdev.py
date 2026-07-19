"""TopDev — dùng API JSON nội bộ, chuyên việc làm IT."""
import requests

from .common import HEADERS, TIMEOUT

API = "https://api.topdev.vn/td/v2/jobs"


def fetch(cfg: dict) -> list[dict]:
    jobs = []
    for query in cfg.get("queries", []):
        params = {
            "fields[job]": "id,title,salary,company,addresses,published,detail_url,job_levels_str",
            "locale": "vi_VN",
            "page": 1,
            "keywords": query,
            "ordering": "jobs_new",
        }
        r = requests.get(API, params=params, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        for item in r.json().get("data", []):
            job_id = item.get("id")
            if not job_id:
                continue
            salary = item.get("salary")
            if isinstance(salary, dict):
                salary = salary.get("value") or salary.get("text") or ""
            addresses = item.get("addresses") or {}
            jobs.append({
                "id": f"topdev:{job_id}",
                "source": "TopDev",
                "title": item.get("title", ""),
                "company": (item.get("company") or {}).get("display_name", ""),
                "url": item.get("detail_url") or "",
                "location": addresses.get("sort_addresses")
                            or addresses.get("address_region_list", ""),
                "salary": salary or "",
                "posted": str(item.get("published") or "")[:10],
                "extra": item.get("job_levels_str", ""),
            })
    return jobs
