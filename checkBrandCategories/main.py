import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import time
from playwright.sync_api import sync_playwright
from utils.config import MAGENTO_CREDENTIALS, DIVISIONS, DIVISIONS_URL, MAGENTO_BRANDS_URL, MAGENTO_CATEGORIES_URL, MAGENTO_COLLECTIONS_URL
from utils.functions import login_magento_admin


def parse_divisions(raw):
    numbers = [n.strip() for n in raw.split(",") if n.strip()]
    return [f"div{n}" for n in numbers]


def extract_grid_rows(page):
    table = page.locator("table[data-role='grid']")
    table.wait_for(state="visible", timeout=15000)

    # Build the header list so cell values can be read by column name instead of position
    headers = table.locator("thead th").evaluate_all(
        "ths => ths.map(th => th.querySelector('.data-grid-cell-content')?.textContent.trim() || '')"
    )

    return table.locator("tbody tr.data-row").evaluate_all(
        """(trs, headers) => trs.map(tr => {
            const cells = Array.from(tr.querySelectorAll(':scope > td'));
            const data = {};
            headers.forEach((h, i) => {
                if (!h) return;
                data[h] = cells[i] ? cells[i].textContent.trim() : '';
            });
            return data;
        })""",
        headers
    )


def wait_for_grid_reload(page):
    # Loading mask that belongs to the grid currently on screen (the page also has one for notifications)
    mask = page.locator("table[data-role='grid']").locator(
        "xpath=ancestor::div[contains(@class,'admin__data-grid-outer-wrap')][1]"
    ).locator(".admin__data-grid-loading-mask")

    # The mask flashes visible then hidden while the grid reloads with the filtered rows
    try:
        mask.wait_for(state="visible", timeout=3000)
    except Exception:
        pass
    mask.wait_for(state="hidden", timeout=20000)
    page.wait_for_load_state("networkidle")


def find_brand_by_uri(page, uri):
    rows = extract_grid_rows(page)
    for row in rows:
        if row.get("Uri", "").strip().lower() == uri.strip().lower():
            return row
    return None


def search_brand(page, division_url, brand_uri):
    page.goto(f"{division_url}{MAGENTO_BRANDS_URL}", wait_until="domcontentloaded")
    page.wait_for_load_state("networkidle")

    page.click("button[data-action='grid-filter-expand']")
    uri_input = page.locator("div[data-part='filter-form'] input[name='uri']")
    uri_input.wait_for(state="visible", timeout=10000)
    uri_input.fill(brand_uri)
    page.click("button[data-action='grid-filter-apply']")
    wait_for_grid_reload(page)

    return find_brand_by_uri(page, brand_uri)


def select_brand_filter(page, brand_id):
    # Locate the filter select that has an option whose value is the brand ID, then pick it
    option = page.locator(f"div[data-part='filter-form'] option[value='{brand_id}']").first
    option.wait_for(state="attached", timeout=10000)
    select_locator = option.locator("xpath=ancestor::select[1]")
    select_locator.wait_for(state="visible", timeout=10000)
    select_locator.select_option(value=str(brand_id))


def get_brand_items(page, division_url, listing_url, brand_id, featured_key="Featured"):
    page.goto(f"{division_url}{listing_url}", wait_until="domcontentloaded")
    page.wait_for_load_state("networkidle")

    page.click("button[data-action='grid-filter-expand']")
    select_brand_filter(page, brand_id)
    page.click("button[data-action='grid-filter-apply']")
    wait_for_grid_reload(page)

    rows = extract_grid_rows(page)
    items = []
    for row in rows:
        # Only keep active (status 1 / Enabled) items
        if row.get("Status", "").strip().lower() not in ("1", "enabled"):
            continue
        items.append({
            "ID": row.get("ID", ""),
            "Name": row.get("Name", ""),
            "Status": row.get("Status", ""),
            "Featured": row.get(featured_key, ""),
        })
    return items


# Request division scope to user
scope = input("Choose an option:\n1. All divisions\n2. Specific divisions\nOption: ").strip()
while scope not in ("1", "2"):
    scope = input("Invalid option. Choose 1 (all divisions) or 2 (specific divisions): ").strip()

if scope == "1":
    selected_divisions = DIVISIONS
else:
    raw = input("Enter divisions separated by commas (e.g. 1,3,4,5,6): ")
    selected_divisions = parse_divisions(raw)
    while not selected_divisions or not all(d in DIVISIONS for d in selected_divisions):
        raw = input("Invalid divisions. Enter divisions separated by commas (e.g. 1,3,4,5,6): ")
        selected_divisions = parse_divisions(raw)

brand_uri = input("Enter the brand URI slug to search (e.g. dior): ").strip()

startTime = time.time()
login_results = {}
brand_results = {}
category_results = {}
collection_results = {}
errors = {}

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)

    for division in selected_divisions:
        page = browser.new_page()
        try:
            credentials = MAGENTO_CREDENTIALS[division]
            admin_url = f"{DIVISIONS_URL[division]}dashboard"
            success = login_magento_admin(page, admin_url, credentials["username"], credentials["password"])
            login_results[division] = success

            if success:
                brand = search_brand(page, DIVISIONS_URL[division], brand_uri)
                brand_results[division] = brand

                if brand:
                    brand_id = brand.get("ID", "")

                    try:
                        category_results[division] = get_brand_items(
                            page, DIVISIONS_URL[division], MAGENTO_CATEGORIES_URL, brand_id
                        )
                    except Exception as e:
                        category_results[division] = []
                        print(f"{division}: categories error - {e}")

                    try:
                        collection_results[division] = get_brand_items(
                            page, DIVISIONS_URL[division], MAGENTO_COLLECTIONS_URL, brand_id, featured_key="Is Featured"
                        )
                    except Exception as e:
                        collection_results[division] = []
                        print(f"{division}: collections error - {e}")
        except Exception as e:
            login_results.setdefault(division, False)
            errors[division] = str(e)
            print(f"{division}: error - {e}")
        finally:
            page.close()

    browser.close()

print("\n--- RESULTS ---")
for division in selected_divisions:
    status = "OK" if login_results[division] else "FAILED"
    print(f"\n{division.upper()}: Login {status}")
    if division in errors:
        print(f"  Error: {errors[division]}")
        continue
    if not login_results[division]:
        continue

    brand = brand_results.get(division)
    if not brand:
        print(f"  No brand found with URI '{brand_uri}'")
        continue

    print(f"  ID: {brand.get('ID', '')}")
    print(f"  Type: {brand.get('Type', '')}")
    print(f"  Status: {brand.get('Status', '')}")
    print(f"  Name: {brand.get('Name', '')}")

    categories = category_results.get(division, [])
    print(f"  Categories ({len(categories)})")
    for item in categories:
        suffix = " (Enabled)" if item["Status"].strip().lower() in ("1", "enabled") else ""
        print(f"    ID: {item['ID']} - {item['Name']}{suffix}")

    collections = collection_results.get(division, [])
    print(f"  Collections ({len(collections)})")
    for item in collections:
        suffix = " (Featured)" if item["Featured"].strip().lower() in ("1", "yes", "true") else ""
        print(f"    ID: {item['ID']} - {item['Name']}{suffix}")

elapsed = time.time() - startTime
print(f"\nTask done in: {elapsed:.2f} seconds")
