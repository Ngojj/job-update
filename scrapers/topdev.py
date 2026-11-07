"""TopDev — dùng API JSON nội bộ, chuyên việc làm IT.

Hai cách quét, gộp lại để không sót:
  1. level_ids: lọc theo cấp bậc do nhà tuyển dụng chọn (1616 = Thực tập,
     12507 = Mới tốt nghiệp) + region_ids (79 = Hồ Chí Minh) → lấy TOÀN BỘ.
  2. queries: từ khoá (API khớp chặt: "fresher" ok, "python intern" ra 0 →
     chỉ nên dùng từ đơn).
Lưu ý: tham số đúng là `keyword` (số ít) — `keywords` bị API bỏ qua.
"""
from concurrent.futures import ThreadPoolExecutor

from .common import get

API = "https://api.topdev.vn/td/v2/jobs"
FIELDS = "id,title,salary,company,addresses,published,detail_url,job_levels_str"


def _page(params: dict, page: int) -> dict:
    return get(API, params={**params, "fields[job]": FIELDS, "locale": "vi_VN",
                            "ordering": "jobs_new", "page": page}).json()


def _crawl(params: dict, max_pages: int) -> list[dict]:
    first = _page(params, 1)
    items = list(first.get("data", []))
    last = min((first.get("meta") or {}).get("last_page", 1), max_pages)
    if last > 1:
        with ThreadPoolExecutor(6) as ex:
            for r in ex.map(lambda p: _page(params, p), range(2, last + 1)):
                items.extend(r.get("data", []))
    return items


def _to_job(item: dict, level_verified: bool) -> dict | None:
    job_id = item.get("id")
    if not job_id:
        return None
    salary = item.get("salary")
    if isinstance(salary, dict):
        salary = salary.get("value") or salary.get("text") or ""
    addresses = item.get("addresses") or {}
    return {
        "id": f"topdev:{job_id}",
        "source": "TopDev",
        "title": item.get("title", ""),
        "company": (item.get("company") or {}).get("display_name", ""),
        "url": item.get("detail_url") or "",
        "location": addresses.get("sort_addresses")
                    or addresses.get("address_region_list", ""),
        "salary": salary or "",
        "posted": str((item.get("published") or {}).get("date", ""))
                  if isinstance(item.get("published"), dict) else str(item.get("published") or ""),
        "extra": item.get("job_levels_str", ""),
        "level_verified": level_verified,
    }


def fetch(cfg: dict) -> list[dict]:
    jobs = []
    max_pages = cfg.get("max_pages", 100)
    region = {"region_ids": str(cfg["region_ids"])} if cfg.get("region_ids") else {}

    for level_id in cfg.get("level_ids", []):
        for item in _crawl({**region, "job_levels_ids": level_id}, max_pages):
            if (j := _to_job(item, level_verified=True)):
                jobs.append(j)

    for query in cfg.get("queries", []):
        for item in _crawl({**region, "keyword": query}, max_pages):
            if (j := _to_job(item, level_verified=False)):
                jobs.append(j)
    return jobs
