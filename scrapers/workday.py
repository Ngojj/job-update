"""Workday — API "cxs" công khai của các trang tuyển dụng *.myworkdayjobs.com.

Dùng cho Intel, Nvidia, Mastercard, Visa, Cisco, Accenture, PwC, Marvell, Medtronic...

config:
  companies:
    - {name: Intel, host: intel.wd1, tenant: intel, site: External}
  search: Vietnam        # từ khoá lọc server-side
Muốn thêm công ty: mở trang tuyển dụng của họ, URL dạng
  https://<host>.myworkdayjobs.com/<site>   (tenant thường = phần đầu của host)
"""
from .common import post

PAGE = 20
VN_MARKERS = ("vietnam", "viet nam", "ho chi minh", "hanoi", "ha noi", "da nang")


def fetch(cfg: dict) -> list[dict]:
    jobs = []
    search = cfg.get("search", "Vietnam")
    max_jobs = cfg.get("max_jobs_per_company", 200)
    for comp in cfg.get("companies", []):
        base = f"https://{comp['host']}.myworkdayjobs.com"
        api = f"{base}/wday/cxs/{comp['tenant']}/{comp['site']}/jobs"
        offset, total = 0, None
        while total is None or offset < min(total, max_jobs):
            data = post(api, json={"limit": PAGE, "offset": offset,
                                   "searchText": search, "appliedFacets": {}}).json()
            total = data.get("total", 0)
            postings = data.get("jobPostings", [])
            for p in postings:
                loc = p.get("locationsText", "")
                path = p.get("externalPath", "")
                # searchText "Vietnam" có thể khớp cả job không ở VN → chặn lại
                if not any(m in (loc + " " + path).lower().replace("_", " ").replace("-", " ")
                           for m in VN_MARKERS):
                    continue
                req = (p.get("bulletFields") or [""])[0]
                jobs.append({
                    "id": f"wd:{comp['tenant']}:{req or path}",
                    "source": comp["name"],
                    "title": p.get("title", ""),
                    "company": comp["name"],
                    "url": f"{base}/en-US/{comp['site']}{path}",
                    "location": loc.replace("_", " "),
                    "salary": "",
                    "posted": p.get("postedOn", ""),
                    "extra": "",
                })
            if not postings:
                break
            offset += PAGE
    return jobs
