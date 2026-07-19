"""ITviec — parse HTML trang danh sách job theo level (fresher/intern)."""
import re

import requests
from bs4 import BeautifulSoup

from .common import HEADERS, TIMEOUT

BASE = "https://itviec.com/it-jobs/{page}"

CITY_RE = re.compile(
    r"(Ho Chi Minh|Hồ Chí Minh|HCM|Ha Noi|Hà Nội|Hanoi|Da Nang|Đà Nẵng|Can Tho|Cần Thơ|Remote)",
    re.IGNORECASE,
)
POSTED_RE = re.compile(r"Posted\s+(.*?\bago\b)|Đăng\s+(.*?\btrước\b)", re.IGNORECASE)


def fetch(cfg: dict) -> list[dict]:
    jobs = []
    for page in cfg.get("pages", []):
        r = requests.get(BASE.format(page=page), headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        for h3 in soup.select("h3[data-url]"):
            url = (h3.get("data-url") or "").split("?")[0]
            if not url:
                continue
            slug = url.rstrip("/").rsplit("/", 1)[-1]
            card = h3.find_parent("div", class_="ipy-2") or h3.parent
            company = ""
            if card:
                company = next(
                    (a.get_text(strip=True) for a in card.select("a[href*='/companies/']")
                     if a.get_text(strip=True)),
                    "",
                )
            card_text = card.get_text(" ", strip=True) if card else ""
            cities = ", ".join(dict.fromkeys(m.group(0) for m in CITY_RE.finditer(card_text)))
            posted_m = POSTED_RE.search(card_text)
            posted = (posted_m.group(1) or posted_m.group(2)) if posted_m else ""
            jobs.append({
                "id": f"itviec:{slug}",
                "source": "ITviec",
                "title": h3.get_text(strip=True),
                "company": company,
                "url": url,
                "location": cities,
                "salary": "",  # ITviec ẩn lương với khách chưa đăng nhập
                "posted": posted,
                "extra": card_text[:500],
            })
    return jobs
