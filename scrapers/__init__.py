from . import (amazon, careerviet, glints, itviec, linkedin, smartrecruiters,
               topcv, topdev, vietnamworks, vng, workday)

# Tên nguồn trong config.yaml  →  hàm fetch(cfg) -> list[job]
SCRAPERS = {
    # Job board
    "vietnamworks": vietnamworks.fetch,
    "topdev": topdev.fetch,
    "itviec": itviec.fetch,
    "linkedin": linkedin.fetch,
    "topcv": topcv.fetch,
    "careerviet": careerviet.fetch,
    "glints": glints.fetch,
    # Trang tuyển dụng trực tiếp của công ty (qua ATS công khai)
    "smartrecruiters": smartrecruiters.fetch,  # Bosch, Grab...
    "workday": workday.fetch,                  # Intel, Nvidia, Cisco, Visa...
    "vng": vng.fetch,                          # VNG / Zalo / ZaloPay / VNGGames
    "amazon": amazon.fetch,                    # Amazon / AWS
}
