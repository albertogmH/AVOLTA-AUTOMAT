import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from playwright.sync_api import sync_playwright

from utils.config import DIVISIONS, DIVISIONS_URL, MAGENTO_CREDENTIALS
from utils.functions import login_magento_admin


STOREVIEW_SELECTOR = ".store-switcher ul.dropdown-menu li.store-switcher-store-view a[data-value]"


def get_storeviews(page, category_url):
	page.goto(category_url, wait_until="domcontentloaded")
	storeviews = page.locator(STOREVIEW_SELECTOR)
	storeviews.first.wait_for(state="attached", timeout=20000)
	return storeviews.evaluate_all(
		"elements => elements.map(el => ({id: el.getAttribute('data-value'), name: el.textContent.trim()}))"
	)


def prompt_divisions():
	while True:
		raw = input("Enter division(s) separated by commas (div1,div2) or 'all': ").strip().lower()
		if raw == "all":
			return DIVISIONS

		divisions = list(dict.fromkeys(value.strip() for value in raw.split(",") if value.strip()))
		invalid = [division for division in divisions if division not in DIVISIONS]
		if divisions and not invalid:
			return divisions

		print(f"Invalid division(s): {', '.join(invalid) if invalid else 'no selection'}. Choose from: {', '.join(DIVISIONS)} or 'all'.")


def prompt_category_id():
	while True:
		category_id = input("Enter category ID: ").strip()
		if category_id.isdigit() and int(category_id) > 0:
			return category_id
		print("Category ID must be a positive integer.")


def get_category_enabled(page, category_id):
	for script_text in page.locator('script[type="text/x-magento-init"]').all_text_contents():
		try:
			config = json.loads(script_text)
		except json.JSONDecodeError:
			continue

		app_config = config.get("*", {}).get("Magento_Ui/js/core/app", {})
		components = app_config.get("components", {})
		category_form = components.get("category_form", {})
		data_source = category_form.get("children", {}).get("category_form_data_source", {})
		category = data_source.get("config", {}).get("data", {})
		if str(category.get("entity_id", "")) != str(category_id):
			continue

		enabled = category.get("is_active")
		if enabled in (True, 1, "1", "true", "True"):
			return True
		if enabled in (False, 0, "0", "false", "False"):
			return False
		raise RuntimeError(f"Category {category_id} has no readable is_active value.")

	raise RuntimeError(f"Category form data for category {category_id} was not found.")


selected_divisions = prompt_divisions()
category_id = prompt_category_id()
results = {}
errors = []

with sync_playwright() as playwright:
	browser = playwright.chromium.launch(headless=True)
	try:
		for division in selected_divisions:
			credentials = MAGENTO_CREDENTIALS[division]
			if not credentials["username"] or not credentials["password"]:
				errors.append(f"{division}: missing credentials; check the local .env configuration.")
				continue

			page = browser.new_page()
			try:
				admin_url = f"{DIVISIONS_URL[division]}dashboard"
				category_url = f"{DIVISIONS_URL[division]}catalog/category/edit/id/{category_id}/"
				storeview_url = category_url + "store/{store_id}/"
				if not login_magento_admin(
					page, admin_url, credentials["username"], credentials["password"]
				):
					raise RuntimeError("Magento login failed.")

				storeviews = get_storeviews(page, category_url)
				if not storeviews:
					raise RuntimeError("No store views were found in the Magento scope selector.")

				results[division] = []
				for storeview in storeviews:
					store_id = storeview["id"]
					store_name = storeview["name"]
					if not store_id or not store_id.isdigit():
						errors.append(f"{division}: could not read a valid store ID for '{store_name}'.")
						continue

					try:
						page.goto(
							storeview_url.format(store_id=store_id),
							wait_until="domcontentloaded",
						)
						if get_category_enabled(page, category_id):
							results[division].append((store_id, store_name))
					except Exception as error:
						errors.append(f"{division} store {store_id} ({store_name}): {error}")
			except Exception as error:
				errors.append(f"{division}: {error}")
			finally:
				page.close()
	finally:
		browser.close()

print(f"Category {category_id} enabled store views:")
for division, storeviews in results.items():
	print(f"\n{division.upper()}:")
	for store_id, store_name in storeviews:
		print(f"{store_id} - {store_name}")

if errors:
	print("\nCould not verify these store views:", file=sys.stderr)
	for error in errors:
		print(f"- {error}", file=sys.stderr)
	raise SystemExit(1)
