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


def load_stores(division=None):
    wb = openpyxl.load_workbook(STORES_XLSX, read_only=True, data_only=True)
    ws = wb.active
    rows = ws.iter_rows(values_only=True)
    headers = [str(h).strip() if h is not None else "" for h in next(rows)]
    idx = {name: headers.index(name) for name in ("division", "store_id", "store_url")}

    stores = []
    for row in rows:
        if division is not None and str(row[idx["division"]]).strip() != str(division):
            continue
        store_url = row[idx["store_url"]]
        if store_url in NULL_VALUES or str(store_url).strip() in NULL_VALUES:
            continue
        stores.append({
            "division": str(row[idx["division"]]).strip(),
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


def normalize_url(url):
    return url.strip().rstrip("/").lower()


def matches_selected_url(store_url, selected_url):
    store_url = normalize_url(store_url)
    selected_url = normalize_url(selected_url)
    return (
        store_url == selected_url
        or store_url.startswith(selected_url + "/")
        or extract_host(store_url) == extract_host(selected_url)
    )


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

selection_mode = input(
    "Select stores:\n"
    "  1. Division with banned sites\n"
    "  2. Specific URLs\n"
    "  3. All divisions\n"
    "Option [1]: "
).strip() or "1"
while selection_mode not in {"1", "2", "3"}:
    selection_mode = input(
        "Invalid option. Select stores:\n"
        "  1. Division with banned sites\n"
        "  2. Specific URLs\n"
        "  3. All divisions\n"
        "Option [1]: "
    ).strip() or "1"

if selection_mode in {"1", "3"}:
    if selection_mode == "1":
        division = input("Enter division (1-10): ").strip()
        while not division.isdigit() or not (1 <= int(division) <= 10):
            division = input("Invalid division. Enter division (1-10): ").strip()
        stores = load_stores(division)
    else:
        stores = load_stores()
        excluded_divisions = parse_list(input(
            "Exclude divisions (comma-separated, e.g. 1, 2, 5; empty for none): "
        ))
        while any(not value.isdigit() or not (1 <= int(value) <= 10) for value in excluded_divisions):
            excluded_divisions = parse_list(input(
                "Invalid divisions. Enter values from 1 to 10 (comma-separated; empty for none): "
            ))
        excluded_divisions = set(excluded_divisions)
        stores = [store for store in stores if store["division"] not in excluded_divisions]

    if not stores:
        print("No stores with a valid URL found")
        sys.exit(1)

    banned_entries = parse_list(input(
        "Enter banned sites or store IDs (comma-separated, e.g. puertoplata.shopdutyfree.com, 172, 175; empty for none): "
    ))
    banned_store_ids = {entry for entry in banned_entries if entry.isdigit()}
    banned_hosts = {extract_host(entry) for entry in banned_entries if not entry.isdigit()}
    allowed_stores = [
        store for store in stores
        if str(store["store_id"]).strip() not in banned_store_ids
        and extract_host(store["store_url"]) not in banned_hosts
    ]

    skipped = [store for store in stores if store not in allowed_stores]
    if skipped:
        print(f"Skipping {len(skipped)} banned store(s):")
        for s in skipped:
            print(f"  - {s['store_url']}")
else:
    selected_urls = parse_list(input("Enter URLs or sites to include (comma-separated): "))
    while not selected_urls:
        selected_urls = parse_list(input("No URLs provided. Enter URLs or sites to include (comma-separated): "))

    stores = load_stores()
    allowed_stores = [
        store for store in stores
        if any(matches_selected_url(store["store_url"], selected_url) for selected_url in selected_urls)
    ]

if not allowed_stores:
    print("No stores match the selected criteria")
    sys.exit(1)

has_redirect = True
is_external = ask_bool("Are the URLs external?", default=False)
localized = ask_bool("Is the slug localized (one per language)?", default=False)
slugs = {}
slug = ""

# For external links the value is used as the full redirect URL, otherwise it is a path slug.
value_label = "full URL" if is_external else "slug"
languages = sorted({s["language"] for s in allowed_stores if s["language"]})
if localized:
    print(f"Languages found: {', '.join(languages) if languages else '(none)'}")
    for lang in languages:
        slugs[lang] = input(f"Enter {value_label} for '{lang}': ").strip()
else:
    slug = input(f"Enter {value_label}: ").strip()

display_in_terms = ask_bool("Show terms in suggested?", default=False)
output_name = input("Enter output file name (empty for date): ").strip()

startTime = time.time()

rows_by_division = {}
for store in allowed_stores:
    value = slugs.get(store["language"], "") if localized else slug
    redirect = value if has_redirect else ""
    division_rows = rows_by_division.setdefault(store["division"], [])
    for term in terms:
        division_rows.append({
            "query_text": term,
            "storeview_id": store["store_id"],
            "store_id": "",
            "website_id": "",
            "redirect": redirect,
            "display_in_terms": 1 if display_in_terms else 0,
            "is_external": 1 if is_external else 0,
        })

suffix = output_name or time.strftime("%d%m%H%M")
if selection_mode == "3":
    output_directory = os.path.join(os.path.dirname(__file__), suffix)
    os.makedirs(output_directory, exist_ok=True)
    output_paths = []
    for division, division_rows in sorted(rows_by_division.items(), key=lambda item: int(item[0])):
        output_path = os.path.join(
            output_directory, f"searchterm_import_DIV{division}{suffix}.csv"
        )
        with open(output_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=COLUMNS)
            writer.writeheader()
            writer.writerows(division_rows)
        output_paths.append(output_path)
else:
    output_path = os.path.join(os.path.dirname(__file__), f"searchterm_import_{suffix}.csv")
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(next(iter(rows_by_division.values())))
    output_paths = [output_path]

total_rows = sum(len(division_rows) for division_rows in rows_by_division.values())
print(f"\nGenerated {total_rows} row(s) from {len(allowed_stores)} store(s) x {len(terms)} term(s)")
if selection_mode == "3":
    for output_path in output_paths:
        division = re.search(r"DIV(\d+)", os.path.basename(output_path)).group(1)
        division_rows = rows_by_division[division]
        division_stores = sum(store["division"] == division for store in allowed_stores)
        print(
            f"DIVISION {division}: {len(division_rows)} row(s) from "
            f"{division_stores} store(s) x {len(terms)} term(s)\n"
            f"Table saved: {output_path}"
        )
else:
    print(f"Table saved to: {output_paths[0]}")

elapsed = time.time() - startTime
print(f"Task completed in: {elapsed:.2f} seconds")