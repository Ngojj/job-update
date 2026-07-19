"""VietnamWorks — dùng API JSON nội bộ mà chính trang web của họ gọi."""
import requests

from .common import HEADERS, TIMEOUT

API = "https://ms.vietnamworks.com/job-search/v1.0/search"
FIELDS = [
    "jobTitle", "alias", "jobId", "companyName", "prettySalary",
    "workingLocations", "approvedOn", "jobFunctionsV3",
]


def fetch(cfg: dict) -> list[dict]:
    jobs = []
    for query in cfg.get("queries", []):
        body = {
            "userId": 0,
            "query": query,
            "filter": [],
            "ranges": [],
            "order": [{"field": "approvedOn", "value": "desc"}],
            "hitsPerPage": 50,
            "page": 0,
            "retrieveFields": FIELDS,
        }
        r = requests.post(API, json=body, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        for item in r.json().get("data", []):
            job_id = item.get("jobId")
            if not job_id:
                continue
            alias = item.get("alias", "").strip("-")
            locations = ", ".join(
                loc.get("cityNameVI") or loc.get("cityName", "")
                for loc in item.get("workingLocations", [])
            )
            func = item.get("jobFunctionsV3") or {}
            jobs.append({
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
                ])),
            })
    return jobs
