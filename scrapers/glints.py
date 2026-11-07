"""Glints Việt Nam — dữ liệu job nằm trong __NEXT_DATA__ của trang tìm kiếm."""
import json
import re

from .common import get

URL = "https://glints.com/vn/opportunities/jobs/explore"
NEXT_DATA_RE = re.compile(r'__NEXT_DATA__[^>]*>(.*?)</script>', re.S)


def _location(loc: dict) -> str:
    # Glints chỉ ghi quận ("Quận 2") — nối thêm tỉnh/thành cha để lọc địa điểm được
    names = [loc.get("formattedName") or loc.get("name") or ""]
    names += [p.get("name", "") for p in loc.get("parents") or []]
    return ", ".join(n for n in names if n)


def _salary(item: dict) -> str:
    for s in item.get("salaries") or []:
        lo, hi = s.get("minAmount"), s.get("maxAmount")
        if lo or hi:
            return f"{lo or ''}-{hi or ''} {s.get('CurrencyCode', '')}/{(s.get('salaryMode') or '').lower()}"
    return ""


def fetch(cfg: dict) -> list[dict]:
    jobs = []
    max_pages = cfg.get("max_pages", 5)
    for query in cfg.get("queries", []):
        for page in range(1, max_pages + 1):
            html = get(URL, params={
                "keyword": query, "country": "VN",
                "locationName": cfg.get("location", "Ho Chi Minh City"),
                "page": page,
            }).text
            m = NEXT_DATA_RE.search(html)
            if not m:
                raise RuntimeError("Glints: không tìm thấy __NEXT_DATA__")
            items = (json.loads(m.group(1))["props"]["pageProps"]
                     .get("initialJobs", {}).get("jobsInPage", []))
            if not items:
                break
            for item in items:
                if item.get("status") not in (None, "OPEN"):
                    continue
                company = (item.get("company") or {}).get("name", "")
                # Glints ghi sẵn loại hình: INTERNSHIP / FULL_TIME... → dùng làm "extra"
                jobs.append({
                    "id": f"glints:{item['id']}",
                    "source": "Glints",
                    "title": item.get("title", ""),
                    "company": company,
                    "url": f"https://glints.com/vn/opportunities/jobs/{item['id']}",
                    "location": _location(item.get("location") or {}),
                    "salary": _salary(item),
                    "posted": (item.get("createdAt") or "")[:10],
                    "extra": (item.get("type") or "").replace("_", " ").lower(),
                    "level_verified": item.get("type") == "INTERNSHIP",
                })
    return jobs
