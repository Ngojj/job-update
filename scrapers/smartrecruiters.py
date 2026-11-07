"""SmartRecruiters — API công khai, dùng cho Bosch, Grab và nhiều tập đoàn khác.

config:
  companies:
    - {id: BoschGroup, name: Bosch}   # id = tên công ty trên jobs.smartrecruiters.com/<id>
  country: vn
Muốn thêm công ty: mở jobs.smartrecruiters.com/<TênCôngTy>, thêm vào danh sách.
"""
from .common import get

API = "https://api.smartrecruiters.com/v1/companies/{company}/postings"
PAGE = 100
# experienceLevel do công ty tự chọn → tin cậy được cho 2 mức này
ENTRY_LEVELS = {"internship", "entry_level"}


def fetch(cfg: dict) -> list[dict]:
    jobs = []
    country = cfg.get("country", "vn")
    for comp in cfg.get("companies", []):
        offset = 0
        while True:
            data = get(API.format(company=comp["id"]),
                       params={"country": country, "limit": PAGE, "offset": offset}).json()
            items = data.get("content", [])
            for item in items:
                loc = item.get("location") or {}
                level = (item.get("experienceLevel") or {}).get("id", "")
                jobs.append({
                    "id": f"sr:{comp['id']}:{item['id']}",
                    "source": comp.get("name", comp["id"]),
                    "title": item.get("name", ""),
                    "company": comp.get("name", comp["id"]),
                    "url": f"https://jobs.smartrecruiters.com/{comp['id']}/{item['id']}",
                    "location": loc.get("city") or loc.get("fullLocation", ""),
                    "salary": "",
                    "posted": (item.get("releasedDate") or "")[:10],
                    "extra": level.replace("_", " "),
                    "level_verified": level in ENTRY_LEVELS,
                })
            offset += PAGE
            if not items or offset >= data.get("totalFound", 0):
                break
    return jobs
