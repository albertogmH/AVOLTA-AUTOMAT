import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import csv
import re
import time
import openpyxl

STORES_XLSX = os.path.join(os.path.dirname(__file__), '..', 'utils', 'stores.xlsx')
NULL_VALUES = {None, "", "NULL", "null"}

COLUMNS = [
    "query_text",
    "storeview_id",
    "store_id",
    "website_id",
    "redirect",
    "display_in_terms",
    "is_external",
]


def parse_list(raw):
    # Split on commas with optional surrounding whitespace, e.g. "a, b" or "a ,b"
    return [item.strip() for item in re.split(r"\s*,\s*", raw) if item.strip()]


def load_stores(division):
    wb = openpyxl.load_workbook(STORES_XLSX, read_only=True, data_only=True)
    ws = wb.active
    rows = ws.iter_rows(values_only=True)
    headers = [str(h).strip() if h is not None else "" for h in next(rows)]
    idx = {name: headers.index(name) for name in ("division", "store_id", "store_url")}

    stores = []
    for row in rows:
        if str(row[idx["division"]]).strip() != str(division):
            continue
        store_url = row[idx["store_url"]]
        if store_url in NULL_VALUES or str(store_url).strip() in NULL_VALUES:
            continue
        stores.append({
            "store_id": row[idx["store_id"]],
            "store_url": str(store_url).strip(),
            "language": extract_language(str(store_url).strip()),
        })
    wb.close()
    return stores


def extract_language(url):
    # e.g. https://cancun.shopdutyfree.com/en/2/ -> en (segment before the numeric store id)
    segments = [seg for seg in re.split(r"/+", url) if seg]
    for i, seg in enumerate(segments):
        if seg.isdigit() and i > 0:
            return segments[i - 1]
    return ""


def extract_host(url):
    # e.g. https://puertoplata.shopdutyfree.com/en/2/ -> puertoplata.shopdutyfree.com
    host = re.sub(r"^[a-zA-Z]+://", "", url.strip())
    return host.split("/")[0].lower()


def ask_bool(prompt, default=False):
    default_label = "y" if default else "n"
    answer = input(f"{prompt} (y/n) [default {default_label}]: ").strip().lower()
    if not answer:
        return default
    return answer == "y"


# Request all inputs
terms = parse_list(input("Enter terms (comma-separated): "))
while not terms:
    terms = parse_list(input("No terms provided. Enter terms (comma-separated): "))

division = input("Enter division (1-10): ").strip()
while not division.isdigit() or not (1 <= int(division) <= 10):
    division = input("Invalid division. Enter division (1-10): ").strip()

banned_urls = parse_list(input("Enter banned sites (comma-separated, e.g. puertoplata.shopdutyfree.com, empty for none): "))

stores = load_stores(division)
if not stores:
    print(f"No stores with a valid URL found for division {division}")
    sys.exit(1)

banned_set = {extract_host(u) for u in banned_urls}
allowed_stores = [s for s in stores if extract_host(s["store_url"]) not in banned_set]

skipped = [s for s in stores if extract_host(s["store_url"]) in banned_set]
if skipped:
    print(f"Skipping {len(skipped)} banned store(s):")
    for s in skipped:
        print(f"  - {s['store_url']}")

if not allowed_stores:
    print("No stores left after applying the banned list")
    sys.exit(1)

is_external = ask_bool("Are the URLs external?", default=False)

# For external links the value is used as the full redirect URL, otherwise it is a path slug.
value_label = "full URL" if is_external else "slug"
localized = ask_bool("Is the slug localized (one per language)?", default=False)

languages = sorted({s["language"] for s in allowed_stores if s["language"]})
slugs = {}
if localized:
    print(f"Languages found: {', '.join(languages) if languages else '(none)'}")
    for lang in languages:
        slugs[lang] = input(f"Enter {value_label} for '{lang}': ").strip()
else:
    slug = input(f"Enter {value_label}: ").strip()

display_in_terms = ask_bool("Show terms in suggested?", default=False)

startTime = time.time()

rows = []
for store in allowed_stores:
    value = slugs.get(store["language"], "") if localized else slug
    redirect = value
    for term in terms:
        rows.append({
            "query_text": term,
            "storeview_id": store["store_id"],
            "store_id": "",
            "website_id": "",
            "redirect": redirect,
            "display_in_terms": 1 if display_in_terms else 0,
            "is_external": 1 if is_external else 0,
        })

output_path = os.path.join(os.path.dirname(__file__), f"search_terms_import.csv")
with open(output_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=COLUMNS)
    writer.writeheader()
    writer.writerows(rows)

print(f"\nGenerated {len(rows)} row(s) from {len(allowed_stores)} store(s) x {len(terms)} term(s)")
print(f"Table saved to: {output_path}")

elapsed = time.time() - startTime
print(f"Task completed in: {elapsed:.2f} seconds")
