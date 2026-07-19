"""Lọc job theo level (intern/fresher), ngành (software/data/AI) và địa điểm."""
import re
import unicodedata


def _pattern(keyword: str) -> re.Pattern:
    # Khớp nguyên từ, không dính vào giữa từ khác (vd: "ml" không khớp "html",
    # "ai" không khớp "domain"). Hỗ trợ keyword có ký tự đặc biệt như c++, .net.
    return re.compile(r"(?<!\w)" + re.escape(keyword.lower()) + r"(?!\w)", re.UNICODE)


def _strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


class JobFilter:
    def __init__(self, cfg: dict):
        f = cfg.get("filters", {})
        self.level = [_pattern(k) for k in f.get("level_keywords", [])]
        # Thêm bản không dấu cho keyword tiếng Việt (vd "thực tập" -> "thuc tap")
        self.level += [_pattern(_strip_accents(k)) for k in f.get("level_keywords", [])
                       if _strip_accents(k) != k.lower()]
        self.field = [_pattern(k) for k in f.get("field_keywords", [])]
        self.field += [_pattern(_strip_accents(k)) for k in f.get("field_keywords", [])
                       if _strip_accents(k) != k.lower()]
        self.exclude = [_pattern(k) for k in f.get("exclude_keywords", [])]
        self.locations = [l.lower() for l in f.get("locations", [])]

    def matches(self, job: dict) -> bool:
        title = job.get("title", "").lower()
        haystack = (title + " " + job.get("extra", "")).lower()

        if any(p.search(title) for p in self.exclude):
            return False
        # Nguồn đã tự lọc level (vd LinkedIn f_E=1,2) thì khỏi cần keyword level
        if not job.get("level_verified") and not any(p.search(haystack) for p in self.level):
            return False
        if not any(p.search(haystack) for p in self.field):
            return False
        if self.locations:
            loc = _strip_accents(job.get("location", "")).lower()
            wanted = [_strip_accents(l) for l in self.locations]
            if not any(w in loc for w in wanted):
                return False
        return True
