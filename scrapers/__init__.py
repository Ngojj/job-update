from . import vietnamworks, topdev, itviec, linkedin

SCRAPERS = {
    "vietnamworks": vietnamworks.fetch,
    "topdev": topdev.fetch,
    "itviec": itviec.fetch,
    "linkedin": linkedin.fetch,
}
