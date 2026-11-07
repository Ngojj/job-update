"""Amazon / AWS — API search.json công khai của amazon.jobs, lọc theo nước Việt Nam."""
from .common import get

API = "https://www.amazon.jobs/en/search.json"
PAGE = 100


def fetch(cfg: dict) -> list[dict]:
    jobs = []
    offset = 0
    while True:
        data = get(API, params={
            "normalized_country_code[]": cfg.get("country_code", "VNM"),
            "result_limit": PAGE,
            "offset": offset,
            "sort": "recent",
        }).json()
        items = data.get("jobs", [])
        for item in items:
            jobs.append({
                "id": f"amazon:{item.get('id_icims') or item.get('id')}",
                "source": "Amazon",
                "title": item.get("title", ""),
                "company": "Amazon",
                "url": "https://www.amazon.jobs" + item.get("job_path", ""),
                "location": item.get("normalized_location") or item.get("location", ""),
                "salary": "",
                "posted": item.get("posted_date", ""),
                "extra": item.get("job_category", ""),
            })
        offset += PAGE
        if not items or offset >= data.get("hits", 0):
            break
    return jobs
