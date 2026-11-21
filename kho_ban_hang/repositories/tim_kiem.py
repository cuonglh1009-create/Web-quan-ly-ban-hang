import unicodedata


def chuan_hoa(value):
    value = unicodedata.normalize("NFD", str(value or "").casefold().replace("đ", "d"))
    return " ".join("".join(c for c in value if not unicodedata.combining(c)).split())
