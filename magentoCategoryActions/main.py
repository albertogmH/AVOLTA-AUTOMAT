"""Check or update category status, name and menu inclusion per store view."""

import json
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

import openpyxl

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from playwright.sync_api import sync_playwright
from utils import config as default_config
from utils.functions import login_magento_admin

STOREVIEW_SELECTOR = ".store-switcher ul.dropdown-menu li.store-switcher-store-view a[data-value]"
ERROR_SELECTOR = ".message-error, [data-ui-id='messages-message-error']"
SAVE_SELECTOR = "#save[data-form-role='save']"
NAME_INPUT_SELECTOR = "[data-index='name'] input[name='name']"
LOADER_SELECTOR = 'div[data-role="spinner"][data-component="category_form.category_form"]'
FIELDSET_SELECTOR = "div.fieldset-wrapper[data-index='general']"
DEFAULT_NAME_SELECTOR = 'input[name="use_default[name]"]'
ENABLED_SELECTOR = "[data-index='is_active'] input[name='is_active']"
CATEGORY_ID_PATTERN = re.compile(r"\(ID:\s*([0-9]+)\)")
FORM_WAIT_MS = 60000
NETWORKIDLE_MS = 5000


class CategoryActionError(RuntimeError):
    pass


def positive_id(value):
    text = str(value)
    if not re.fullmatch(r"[0-9]+", text) or int(text) <= 0:
        raise CategoryActionError("Expected a positive Magento ID.")
    return str(int(text))


def normalize_division(value):
    match = re.fullmatch(r"(?:div)?([1-9][0-9]*)", str(value).strip().lower())
    if not match:
        raise CategoryActionError("Database contains an ambiguous division.")
    return "div" + match.group(1)


def division_label(division):
    return "DIVISION " + normalize_division(division)[3:]


@dataclass(frozen=True)
class RenameItem:
    store_id: str
    name: str
    title: str


ACTIONS = {"1": "check", "2": "rename", "3": "toggle", "4": "menu"}


def prompt_action():
    while True:
        value = input("Choose an option:\n1. Check enabled\n2. Rename category\n"
                      "3. Enable/Disable category\n4. Include/Exclude menu\nOption: ").strip()
        if value in ACTIONS:
            return ACTIONS[value]
        print("Choose 1, 2, 3 or 4.")


def prompt_enabled_state():
    while True:
        value = input("Set category to:\n1. Enabled\n2. Disabled\nOption: ").strip()
        if value in ("1", "2"):
            return value == "1"
        print("Choose 1 or 2.")


def prompt_menu_state():
    while True:
        value = input("Set category to:\n1. Include in Menu\n2. Exclude from Menu\nOption: ").strip()
        if value in ("1", "2"):
            return value == "1"
        print("Choose 1 or 2.")


def prompt_yes_no(message):
    while True:
        answer = input(message).strip().lower()
        if answer in ("y", "n"):
            return answer == "y"
        print("Choose y or n.")


def prompt_divisions(available=None):
    if available is None:
        available = default_config.DIVISIONS
    while True:
        raw = input("Enter division(s) separated by commas (1,2) or 'all': ").strip().lower()
        if raw == "all":
            return list(available)
        try:
            divisions = list(dict.fromkeys(
                normalize_division(value) for value in raw.split(",") if value.strip()))
        except CategoryActionError:
            divisions = []
        if divisions and all(division in available for division in divisions):
            return divisions
        print(f"Choose from: {', '.join(division_label(division) for division in available)} or 'all'.")


def prompt_category_id(message="Enter category ID: "):
    while True:
        try:
            return positive_id(input(message).strip())
        except CategoryActionError:
            print("Category ID must be a positive integer.")


def prompt_category_ids(divisions):
    if len(divisions) > 1 and prompt_yes_no("Use a different category ID for each division? (y/n): "):
        return {division: prompt_category_id(f"{division_label(division)} - Enter category ID: ")
                for division in divisions}
    category_id = prompt_category_id()
    return {division: category_id for division in divisions}


def store_host(value):
    parsed = urlsplit(value if "://" in value else "https://" + value)
    if not parsed.hostname or parsed.username or parsed.password:
        raise CategoryActionError("Enter a valid site URL or store ID.")
    return parsed.hostname.lower()


def prompt_exclusions():
    while True:
        entries = [entry.strip() for entry in input(
            "Enter banned sites or store IDs (comma-separated, e.g. "
            "madrid.shopdutyfree.com, 172; empty for none): "
        ).split(",") if entry.strip()]
        try:
            store_ids = {positive_id(entry) for entry in entries if entry.isdigit()}
            hosts = {store_host(entry) for entry in entries if not entry.isdigit()}
            return store_ids, hosts
        except (CategoryActionError, ValueError):
            print("Enter valid site URLs or positive store IDs.")


def load_store_details(divisions):
    workbook = openpyxl.load_workbook(ROOT / "utils" / "stores.xlsx", read_only=True, data_only=True)
    details = {division: {} for division in divisions}
    try:
        rows = workbook.active.iter_rows(values_only=True)
        headers = [str(value).strip() for value in next(rows)]
        for values in rows:
            row = dict(zip(headers, values))
            try:
                division = normalize_division(row.get("division"))
            except CategoryActionError:
                continue
            if division not in details or str(row.get("store_id")) == "0":
                continue
            store_id = positive_id(row["store_id"])
            url = str(row.get("store_url") or "").strip()
            if url.lower() in ("", "null"):
                continue
            host = store_host(url)
            parts = urlsplit(url if "://" in url else "https://" + url).path.strip("/").split("/")
            language = parts[-2].lower() if len(parts) >= 2 and parts[-1].isdigit() else ""
            if not re.fullmatch(r"[a-z]{2,3}(?:-[a-z]{2,4})?", language):
                language = ""
            detail = (host, language, str(row.get("name") or store_id))
            if store_id in details[division] and details[division][store_id] != detail:
                raise CategoryActionError(f"{division_label(division)} store {store_id}: conflicting store mappings.")
            details[division][store_id] = detail
    finally:
        workbook.close()
    return details


def filter_storeviews(storeviews, details, banned_ids, banned_hosts):
    allowed = []
    for store_id, name in storeviews:
        if store_id in banned_ids:
            print(f"Skipping banned store {store_id} - {name}.")
            continue
        if banned_hosts and store_id not in details:
            raise CategoryActionError(f"Cannot check URL exclusions for store {store_id}; no writes attempted.")
        if banned_hosts and details[store_id][0] in banned_hosts:
            print(f"Skipping banned store {store_id} - {name}.")
            continue
        allowed.append((store_id, name))
    return allowed


def collect_renames(storeviews, details):
    if not storeviews:
        return []
    languages = sorted({details[store_id][1] for store_id, _ in storeviews
                        if details[store_id][1]})
    print(f"Languages found: {', '.join(languages) if languages else '(unknown)'}")
    localized = prompt_yes_no("Localize category name (one per language)? (y/n): ")
    plan = []
    groups = {}
    for store_id, name in storeviews:
        language = details[store_id][1]
        group = (language or f"store {store_id} - {name}") if localized else "all store views"
        groups.setdefault(group, []).append((store_id, name))
    for language, stores in groups.items():
        while True:
            title = input(f"{language.upper()} Category name (leave it blank to skip): ")
            if not title.strip():
                break
            if len(title) > 255:
                print("Category names must not exceed 255 characters.")
                continue
            plan.extend(RenameItem(store_id, name, title) for store_id, name in stores)
            break
    return plan


def confirm_renames(category_id, division, plan):
    print(f"Intended changes for category {category_id} ({division_label(division)}):")
    for item in plan:
        print(f"{item.store_id} - {item.name} -> {json.dumps(item.title, ensure_ascii=False)}")
    return prompt_yes_no("Save these changes? (y/n): ")


def wait_for_category_form(page, timeout=FORM_WAIT_MS, writable=True):
    # Magento shows a loader and then renders the form; each wait returns at once if already satisfied.
    login = page.locator("input#username")
    try:
        page.wait_for_load_state("networkidle", timeout=min(timeout, NETWORKIDLE_MS))
    except Exception:
        pass
    steps = [
        ("Category form loader did not finish.", page.locator(LOADER_SELECTOR), "hidden", False),
        ("General fieldset did not load.", page.locator(FIELDSET_SELECTOR), "visible", True),
        ("Category name field did not load.", page.locator(NAME_INPUT_SELECTOR), "visible", True),
    ]
    if writable:
        steps += [
            ("Use Default Value checkbox did not load.", page.locator(DEFAULT_NAME_SELECTOR), "attached", True),
            ("Store id field did not load.", page.locator('input[name="store_id"]'), "attached", True),
        ]
    for message, component, state, or_login in steps:
        try:
            (component.or_(login) if or_login else component).first.wait_for(state=state, timeout=timeout)
        except Exception:
            raise CategoryActionError(message) from None
        if or_login and login.count() == 1:
            raise CategoryActionError("Magento login is required.")


def require_edit_page(page, edit_url):
    # Magento answers an unknown category id with a silent redirect to the category index.
    expected = urlsplit(edit_url)
    match = re.fullmatch(r"(.*/)catalog/category/edit/id/([0-9]+)/(?:store/([0-9]+)/)?", expected.path)
    base_url = f"{expected.scheme}://{expected.netloc}{match.group(1)}"
    actual = urlsplit(page.url)
    if (not actual.username and not actual.password
            and (actual.scheme, actual.netloc) == (expected.scheme, expected.netloc)
            and re.fullmatch(re.escape(match.group(1)) + r"catalog/category/index/(?:store/[0-9]+/)?(?:key/[A-Za-z0-9_-]+/)?",
                             actual.path)):
        raise CategoryActionError(f"Category {match.group(2)} was not found in this division "
                                  "(Magento redirected to the category index).")
    validate_category_edit_url(page.url, base_url, match.group(2), match.group(3))


def get_storeviews(page, category_url, form_timeout=FORM_WAIT_MS):
    page.goto(category_url, wait_until="domcontentloaded")
    require_edit_page(page, category_url)
    wait_for_category_form(page, form_timeout, writable=False)
    storeviews = page.locator(STOREVIEW_SELECTOR)
    try:
        storeviews.first.wait_for(state="attached", timeout=form_timeout)
    except Exception:
        raise CategoryActionError("Store view list did not load in time.") from None
    result = storeviews.evaluate_all(
        "elements => elements.map(el => ({id: el.getAttribute('data-value'), name: el.textContent.trim()}))"
    )
    if not result:
        raise CategoryActionError("No store views found.")
    return result


def verify_page_category(page, category_id):
    # The loaded form no longer exposes its init data; the heading/title carries "(ID: N)".
    ids = {found[-1] for text in page.locator("h1.page-title").all_text_contents()
           if (found := CATEGORY_ID_PATTERN.findall(text))}
    if not ids:
        ids = {found[-1] for found in [CATEGORY_ID_PATTERN.findall(page.title())] if found}
    if len(ids) != 1 or ids != {str(category_id)}:
        raise CategoryActionError("Requested category form data was not found.")


def get_category_enabled(page, category_id):
    verify_page_category(page, category_id)
    checkbox = page.locator(ENABLED_SELECTOR)
    if checkbox.count() != 1:
        raise CategoryActionError("Category has no readable is_active value.")
    return checkbox.is_checked()


def category_url(base_url, category_id, store_id=None):
    result = base_url.rstrip("/") + f"/catalog/category/edit/id/{positive_id(category_id)}/"
    if store_id is not None:
        result += f"store/{positive_id(store_id)}/"
    return result


def validate_category_edit_url(url, base_url, category_id, store_id):
    expected = urlsplit(category_url(base_url, category_id, store_id))
    actual = urlsplit(url)
    if (actual.username or actual.password
            or (actual.scheme, actual.netloc) != (expected.scheme, expected.netloc)
            or not re.fullmatch(re.escape(expected.path) + r"(?:key/[A-Za-z0-9_-]+/)?", actual.path)
            or actual.query or actual.fragment):
        raise CategoryActionError("Unexpected category/store URL or login redirect.")


def validate_post_save_url(url, base_url, category_id, store_id):
    # Magento redirects a save with _current params, so id/store may come in either order.
    category_id, store_id = positive_id(category_id), positive_id(store_id)
    base, actual = urlsplit(base_url), urlsplit(url)
    if (actual.username or actual.password or (actual.scheme, actual.netloc) != (base.scheme, base.netloc)
            or actual.query or actual.fragment):
        raise CategoryActionError("Unexpected category/store URL or login redirect.")
    prefix = re.escape(base.path.rstrip("/") + "/catalog/category/")
    if re.fullmatch(prefix + r"index/(?:store/[0-9]+/)?(?:key/[A-Za-z0-9_-]+/)?", actual.path):
        raise CategoryActionError(f"Category {category_id} was not shown after save "
                                  "(Magento redirected to the category index).")
    match = re.fullmatch(prefix + r"edit/((?:[a-z]+/[A-Za-z0-9_-]+/)+)", actual.path)
    parts = match.group(1).split("/")[:-1] if match else []
    segments = dict(zip(parts[::2], parts[1::2]))
    if (not match or len(segments) != len(parts) // 2 or not {"id", "store"} <= set(segments)
            or set(segments) - {"id", "store", "key"}
            or segments["id"] != category_id or segments["store"] != store_id):
        raise CategoryActionError("Unexpected category/store URL or login redirect.")


def verify_category_url(page, base_url, category_id, store_id, validate_url=validate_category_edit_url):
    validate_url(page.url, base_url, category_id, store_id)
    if page.locator("input#username").count():
        raise CategoryActionError("Magento login is required.")
    verify_page_category(page, category_id)


def verify_scope(page, base_url, category_id, store_id, timeout=20000, validate_url=validate_category_edit_url):
    verify_category_url(page, base_url, category_id, store_id, validate_url)
    hidden = page.locator('input[name="store_id"]')
    hidden.first.wait_for(state="attached", timeout=timeout)
    if not hidden.count() or any(value != str(store_id) for value in hidden.evaluate_all(
            "elements => elements.map(element => element.value)")):
        raise CategoryActionError("Store form scope does not match the requested store.")
    switcher = page.locator('input[data-role="store-view-id"]')
    if any(value != str(store_id) for value in switcher.evaluate_all(
            "elements => elements.map(element => element.value)")):
        raise CategoryActionError("Store switcher scope does not match the requested store.")


def name_controls(page, timeout=20000):
    page.locator(NAME_INPUT_SELECTOR).first.wait_for(
        state="attached", timeout=timeout
    )
    preferred = page.locator(".fieldset-wrapper[data-index='general'] [data-index='name']")
    container = preferred if preferred.count() else page.locator(".admin__field[data-index='name']")
    if container.count() != 1:
        raise CategoryActionError("Category Name container is missing or ambiguous.")
    name = container.locator('input[name="name"]')
    default = container.locator('input[type="checkbox"][name="use_default[name]"]')
    if name.count() != 1 or default.count() != 1:
        raise CategoryActionError("Category Name controls are missing or ambiguous.")
    return name, default


def open_store_form(page, base_url, category_id, store_id, timeout, form_timeout):
    edit_url = category_url(base_url, category_id, store_id)
    page.goto(edit_url, wait_until="domcontentloaded")
    require_edit_page(page, edit_url)
    wait_for_category_form(page, form_timeout)
    verify_scope(page, base_url, category_id, store_id, timeout)


def save_and_reload(page, base_url, category_id, store_id, timeout, on_save_attempt, form_timeout):
    save = page.locator(SAVE_SELECTOR)
    save.wait_for(state="visible", timeout=timeout)
    verify_scope(page, base_url, category_id, store_id, timeout)
    if on_save_attempt is not None:
        on_save_attempt()
    # The page's own Save button does an AJAX validate, then a form POST that 302s back to the edit page.
    try:
        with page.expect_navigation(wait_until="domcontentloaded", timeout=form_timeout):
            save.click(timeout=timeout)
    except Exception:
        raise CategoryActionError("Save did not complete: page did not reload.") from None
    validate_post_save_url(page.url, base_url, category_id, store_id)
    wait_for_category_form(page, form_timeout)
    verify_scope(page, base_url, category_id, store_id, timeout, validate_post_save_url)
    if page.locator(ERROR_SELECTOR).evaluate_all(
            "elements => elements.some(element => element.getClientRects().length)"):
        raise CategoryActionError("Magento reported a save error.")


def rename_store(page, base_url, category_id, store_id, title, timeout=20000, on_save_attempt=None,
                 form_timeout=FORM_WAIT_MS):
    if not title.strip() or len(title) > 255:
        raise CategoryActionError("Invalid category title; no write attempted.")
    category_id, store_id = positive_id(category_id), positive_id(store_id)
    open_store_form(page, base_url, category_id, store_id, timeout, form_timeout)
    name, default = name_controls(page, timeout)
    if default.is_checked():
        default.uncheck(timeout=timeout)
    name.fill(title, timeout=timeout)
    name.blur(timeout=timeout)
    if name.input_value() != title or default.is_checked():
        raise CategoryActionError("Category Name did not accept the requested override.")
    save_and_reload(page, base_url, category_id, store_id, timeout, on_save_attempt, form_timeout)
    name, default = name_controls(page, timeout)
    if name.input_value() != title or default.is_checked():
        raise CategoryActionError("Saved category name/default state did not persist.")


def category_flag_input(page, field, timeout):
    checkbox = page.locator(f"[data-index='{field}'] input[name='{field}']")
    checkbox.first.wait_for(state="attached", timeout=timeout)
    if checkbox.count() != 1:
        raise CategoryActionError(f"Category {field} control is missing or ambiguous.")
    return checkbox


def set_store_flags(page, base_url, category_id, store_id, targets, timeout=20000, on_save_attempt=None,
                    form_timeout=FORM_WAIT_MS):
    category_id, store_id = positive_id(category_id), positive_id(store_id)
    open_store_form(page, base_url, category_id, store_id, timeout, form_timeout)
    changed = []
    for field, target in targets.items():
        checkbox = category_flag_input(page, field, timeout)
        if checkbox.is_checked() == target:
            continue
        default = page.locator(f"[data-index='{field}'] input[name='use_default[{field}]']")
        if default.count() != 1:
            raise CategoryActionError(f"Category {field} default control is missing or ambiguous.")
        if default.is_checked():
            default.uncheck(timeout=timeout)
        if checkbox.is_checked() != target:
            switch = page.locator(f"[data-index='{field}'] label.admin__actions-switch-label")
            if switch.count() != 1:
                raise CategoryActionError(f"Category {field} switch is missing or ambiguous.")
            switch.click(timeout=timeout)
        if checkbox.is_checked() != target or default.is_checked():
            raise CategoryActionError(f"Category {field} did not accept the requested override.")
        changed.append(field)
    if not changed:
        return False
    save_and_reload(page, base_url, category_id, store_id, timeout, on_save_attempt, form_timeout)
    for field, target in targets.items():
        if category_flag_input(page, field, timeout).is_checked() != target:
            raise CategoryActionError(f"Saved category {field} value did not persist.")
        if field in changed:
            default = page.locator(f"[data-index='{field}'] input[name='use_default[{field}]']")
            if default.count() != 1 or default.is_checked():
                raise CategoryActionError(f"Saved category {field} override did not persist.")
    return True


def set_store_enabled(page, base_url, category_id, store_id, enabled, timeout=20000, on_save_attempt=None,
                      form_timeout=FORM_WAIT_MS, include_in_menu=None):
    targets = {"is_active": enabled}
    if include_in_menu is not None:
        targets["include_in_menu"] = include_in_menu
    return set_store_flags(page, base_url, category_id, store_id, targets, timeout, on_save_attempt,
                           form_timeout)


def set_store_menu(page, base_url, category_id, store_id, include_in_menu, timeout=20000,
                   on_save_attempt=None, form_timeout=FORM_WAIT_MS):
    return set_store_flags(page, base_url, category_id, store_id, {"include_in_menu": include_in_menu},
                           timeout, on_save_attempt, form_timeout)


def report_error(division, category_id, store_id, error, status=None):
    scope = f"{division_label(division)} category {category_id}"
    if store_id is not None and re.fullmatch(r"[0-9]+", str(store_id)):
        scope += f" store {store_id}"
    reason = str(error) if isinstance(error, CategoryActionError) else "Browser/login/save verification failed."
    line = f"{scope}: {reason}" + (f" [{status}]" if status else "")
    print(line, file=sys.stderr)
    return line


def close_quietly(resource):
    try:
        resource.close()
    except Exception:
        pass


def valid_storeviews(storeviews, division, category_id, errors):
    result = []
    for storeview in storeviews:
        try:
            result.append((positive_id(storeview["id"]), storeview["name"]))
        except Exception as error:
            errors.append(report_error(division, category_id, storeview.get("id"), error))
    return result


def status_lines(label, stores):
    lines = [f"{label} ({len(stores)}):"]
    lines += [f"  {store_id} - {name}" for store_id, name in stores]
    lines.append(f"{label} IDs: {','.join(store_id for store_id, _ in stores)}")
    return lines


def check_enabled_stores(page, base_url, division, category_id, storeviews, errors, form_timeout=FORM_WAIT_MS):
    enabled_stores = []
    disabled_stores = []
    for store_id, name in storeviews:
        try:
            edit_url = category_url(base_url, category_id, store_id)
            page.goto(edit_url, wait_until="domcontentloaded")
            require_edit_page(page, edit_url)
            wait_for_category_form(page, form_timeout, writable=False)
            verify_category_url(page, base_url, category_id, store_id)
            (enabled_stores if get_category_enabled(page, category_id) else disabled_stores).append(
                (store_id, name))
        except Exception as error:
            errors.append(report_error(division, category_id, store_id, error))
    return status_lines("Enabled", enabled_stores) + status_lines("Disabled", disabled_stores)


def main(default_action=None, config=None):
    config = default_config if config is None else config
    start_time = time.monotonic()
    results = {}
    errors = []
    verified_saves = 0

    try:
        action = default_action or prompt_action()
        if action not in ("check", "rename", "toggle", "menu"):
            raise CategoryActionError("Choose check, rename, toggle or menu.")
        divisions = prompt_divisions(config.DIVISIONS)
        category_ids = prompt_category_ids(divisions)
        banned_ids, banned_hosts = set(), set()
        store_details = {division: {} for division in divisions}
        rename_plans = {}
        if action != "check":
            banned_ids, banned_hosts = prompt_exclusions()
            if action == "rename" or banned_hosts:
                store_details = load_store_details(divisions)
        if action == "rename":
            for division in divisions:
                print(f"\n{division_label(division)} - Category {category_ids[division]}")
                details = store_details[division]
                candidates = filter_storeviews(
                    [(store_id, detail[2]) for store_id, detail in details.items()],
                    details, banned_ids, banned_hosts)
                rename_plans[division] = collect_renames(candidates, details)
            if not any(rename_plans.values()):
                print("No changes requested; browser/login skipped.")
                return 0
        target_enabled = None
        target_menu = None
        if action in ("toggle", "menu"):
            if action == "toggle":
                target_enabled = prompt_enabled_state()
                state = "Enabled" if target_enabled else "Disabled"
                if target_enabled and prompt_yes_no("Also mark Include in Menu? (y/n): "):
                    target_menu = True
                    state += " + Include in Menu"
            else:
                target_menu = prompt_menu_state()
                state = "Include in Menu" if target_menu else "Exclude from Menu"
            for division in divisions:
                print(f"{division_label(division)} - Category {category_ids[division]} -> {state}")
            if not prompt_yes_no("Apply these changes to non-excluded store views? (y/n): "):
                print("No changes requested; browser/login skipped.")
                return 0
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=False)
            try:
                for division in divisions:
                    if action == "rename" and not rename_plans[division]:
                        continue
                    category_id = category_ids[division]
                    context = None
                    results[division] = []
                    try:
                        context = browser.new_context(service_workers="block")
                        credentials = config.MAGENTO_CREDENTIALS[division]
                        if not credentials["username"] or not credentials["password"]:
                            raise CategoryActionError("Missing local Magento credentials.")
                        base_url = config.DIVISIONS_URL[division]
                        page = context.new_page()
                        jobs = []
                        try:
                            login_failures = []
                            if not login_magento_admin(
                                    page, base_url + "dashboard", credentials["username"],
                                    credentials["password"], timeout=60000,
                                    on_failure=login_failures.append):
                                raise CategoryActionError(login_failures[-1] if login_failures
                                                          else "Magento authentication was not confirmed.")
                            storeviews = valid_storeviews(
                                get_storeviews(page, category_url(base_url, category_id)),
                                division, category_id, errors)
                            if action == "check":
                                results[division] = check_enabled_stores(
                                    page, base_url, division, category_id, storeviews, errors)
                            else:
                                storeviews = filter_storeviews(
                                    storeviews, store_details[division], banned_ids, banned_hosts)
                                if action in ("toggle", "menu"):
                                    jobs = [(store_id, None) for store_id, _ in storeviews]
                                else:
                                    selected_ids = {store_id for store_id, _ in storeviews}
                                    plan = [item for item in rename_plans[division]
                                            if item.store_id in selected_ids]
                                    if not plan:
                                        print(f"No requested store views found in the selector for {division_label(division)}.")
                                    elif confirm_renames(category_id, division, plan):
                                        jobs = [(item.store_id, item.title) for item in plan]
                        finally:
                            close_quietly(page)
                        for store_id, title in jobs:
                            attempted = []
                            store_page = None
                            try:
                                store_page = context.new_page()
                                if action == "rename":
                                    rename_store(store_page, base_url, category_id, store_id, title,
                                                 on_save_attempt=lambda: attempted.append(True))
                                    message = "saved and verified."
                                else:
                                    if action == "toggle":
                                        changed = set_store_enabled(
                                            store_page, base_url, category_id, store_id, target_enabled,
                                            on_save_attempt=lambda: attempted.append(True),
                                            include_in_menu=target_menu)
                                    else:
                                        changed = set_store_menu(
                                            store_page, base_url, category_id, store_id, target_menu,
                                            on_save_attempt=lambda: attempted.append(True))
                                    message = ("saved and verified." if changed else
                                               "already has the requested value; no change.")
                                if attempted:
                                    verified_saves += 1
                                results[division].append(f"store {store_id}: {message}")
                            except Exception as error:
                                status = ("save may have committed (unverified)" if attempted
                                          else "not transmitted")
                                errors.append(report_error(division, category_id, store_id, error, status))
                                results[division].append(f"store {store_id}: FAILED [{status}].")
                            finally:
                                if store_page is not None:
                                    close_quietly(store_page)
                    except Exception as error:
                        errors.append(report_error(division, category_id, None, error,
                                                   "not transmitted" if action != "check" else None))
                    finally:
                        if context is not None:
                            close_quietly(context)
            finally:
                browser.close()
        return 1 if errors else 0
    except (EOFError, KeyboardInterrupt):
        errors.append("Cancelled.")
        print("Cancelled.", file=sys.stderr)
        return 1
    except CategoryActionError as error:
        errors.append("Category action failed.")
        print(str(error), file=sys.stderr)
        return 1
    except Exception:
        errors.append("Category action failed.")
        print("Category action failed; check local prerequisites. No automatic retry.", file=sys.stderr)
        return 1
    finally:
        print("\n--- RESULTS ---")
        for division, entries in results.items():
            print(f"\n{division_label(division)}:")
            for entry in entries:
                print(f"  {entry}")
        print(f"Errors: {len(errors)}; verified saves: {verified_saves}")
        for error in errors:
            print(f"  FAILED: {error}")
        print(f"Task done in: {time.monotonic() - start_time:.2f} seconds")


if __name__ == "__main__":
    raise SystemExit(main())