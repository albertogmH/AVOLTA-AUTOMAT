import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import re
import openpyxl

STORES_XLSX = os.path.join(os.path.dirname(__file__), '..', 'utils', 'stores.xlsx')
NULL_VALUES = {None, "", "NULL", "null"}


def parse_list(raw):
    return [item.strip() for item in re.split(r"\s*,\s*", raw) if item.strip()]


def normalize(url):
    return url.strip().rstrip("/").lower()


def load_stores():
    wb = openpyxl.load_workbook(STORES_XLSX, read_only=True, data_only=True)
    ws = wb.active
    rows = ws.iter_rows(values_only=True)
    headers = [str(h).strip() if h is not None else "" for h in next(rows)]
    idx = {name: headers.index(name) for name in ("store_id", "store_url")}

    stores = []
    for row in rows:
        store_url = row[idx["store_url"]]
        if store_url in NULL_VALUES or str(store_url).strip() in NULL_VALUES:
            continue
        stores.append({
            "store_id": row[idx["store_id"]],
            "store_url": str(store_url).strip(),
        })
    wb.close()
    return stores


def main():
    raw = input("Enter store URLs separated by commas: ")
    inputs = parse_list(raw)
    if not inputs:
        print("No URLs provided.")
        return

    stores = load_stores()

    for query in inputs:
        prefix = normalize(query)
        matches = [s for s in stores if normalize(s["store_url"]).startswith(prefix)]
        print(f"\n{query}")
        if not matches:
            print("  No matches found.")
            continue
        for s in matches:
            print(f"  {s['store_id']} -> {s['store_url']}")

    print("\nStore IDs:", ",".join(
        str(s["store_id"])
        for query in inputs
        for s in stores
        if normalize(s["store_url"]).startswith(normalize(query))
    ))


if __name__ == "__main__":
    main()
