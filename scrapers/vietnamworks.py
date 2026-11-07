"""VietnamWorks — dùng API JSON nội bộ mà chính trang web của họ gọi.

Hai cách quét, gộp lại để không sót:
  1. level_ids: lọc theo cấp bậc do NHÀ TUYỂN DỤNG chọn (1 = Fresher/Entry level,
     8 = Intern/Student) + thành phố → lấy TOÀN BỘ job thuộc level đó.
  2. queries: tìm theo từ khoá (bắt các job ghi "fresher/intern" trong tiêu đề
     nhưng chọn nhầm level khác).
"""
from .common import post

API = "https://ms.vietnamworks.com/job-search/v1.0/search"
FIELDS = [
    "jobTitle", "alias", "jobId", "companyName", "prettySalary",
    "workingLocations", "approvedOn", "jobFunctionsV3", "jobLevelVI", "jobLevel",
]
PER_PAGE = 50


def _search(query: str, filters: list, max_pages: int):
    for page in range(max_pages):
        body = {
            "userId": 0,
            "query": query,
            "filter": filters,
            "ranges": [],
            "order": [{"field": "approvedOn", "value": "desc"}],
            "hitsPerPage": PER_PAGE,
            "page": page,
            "retrieveFields": FIELDS,
        }
        data = post(API, json=body).json()
        yield from data.get("data", [])
        if page + 1 >= (data.get("meta") or {}).get("nbPages", 0):
            break


def _to_job(item: dict, level_verified: bool) -> dict | None:
    job_id = item.get("jobId")
    if not job_id:
        return None
    alias = item.get("alias", "").strip("-")
    locations = ", ".join(
        loc.get("cityNameVI") or loc.get("cityName", "")
        for loc in item.get("workingLocations", [])
    )
    func = item.get("jobFunctionsV3") or {}
    return {
        "id": f"vietnamworks:{job_id}",
        "source": "VietnamWorks",
        "title": item.get("jobTitle", ""),
        "company": item.get("companyName", ""),
        "url": f"https://www.vietnamworks.com/{alias}--{job_id}-jv",
        "location": locations,
        "salary": item.get("prettySalary", ""),
        "posted": (item.get("approvedOn") or "")[:10],
        "extra": " ".join(filter(None, [
            func.get("jobFunctionV3Name", ""),
            func.get("jobFunctionV3NameVI", ""),
            item.get("jobLevel", ""),
        ])),
        "level_verified": level_verified,
    }


def fetch(cfg: dict) -> list[dict]:
    jobs = []
    max_pages = cfg.get("max_pages", 6)
    city = [{"field": "workingLocations.cityId", "value": str(cfg["city_id"])}] \
        if cfg.get("city_id") else []

    for level_id in cfg.get("level_ids", []):
        flt = [{"field": "jobLevelId", "value": str(level_id)}] + city
        for item in _search("", flt, max_pages * 2):
            if (j := _to_job(item, level_verified=True)):
                jobs.append(j)

    for query in cfg.get("queries", []):
        for item in _search(query, city, max_pages):
            if (j := _to_job(item, level_verified=False)):
                jobs.append(j)
    return jobs
