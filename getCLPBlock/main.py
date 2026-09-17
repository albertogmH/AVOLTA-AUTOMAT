import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import time
from playwright.sync_api import sync_playwright
from utils.config import CREDENTIALS, DIVISIONS, DIVISIONS_ADMIN, DIVISIONS_CLP, EMPTY_CLP_VALUES, DEFAULT_CLP_LABEL


def getDefaultValue(page, url):
    page.goto(url)
    page.wait_for_load_state("networkidle")
    contentSection = page.locator(".fieldset-wrapper.admin__collapsible-block-wrapper:has(span:text('Content'))")
    try:
        contentSection.wait_for(state="visible", timeout=6000)
    except Exception:
        print("Default - Content not found")
        return ''
    contentSection.click()
    selectLocator = page.locator(
        ".fieldset-wrapper.admin__collapsible-block-wrapper:has(span:text('Content')) "
        ".admin__field:last-child select"
    )
    try:
        selectLocator.wait_for(state="visible", timeout=6000)
    except Exception:
        print("Default - Select not found")
        return ''
    return selectLocator.evaluate("el => el.options[el.selectedIndex]?.text ?? el.value")

# Request division to user
division = input("Enter division (div1, div2, ..., div10): ")
while division not in DIVISIONS:
    division = input("Invalid division.\nEnter division (div1, div2, ..., div10): ")

# Request category ID to user
categoryId = input("Enter category ID (84): ")
while not categoryId.isdigit():
    categoryId = input("Invalid category ID.\nEnter category ID (84): ")

defaultValue = ''
blocks = []
blocksDetail = {}
ids = []

startTime = time.time()

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    adminURL = DIVISIONS_ADMIN[division]
    divisionURL = DIVISIONS_CLP[division]

    # Login to the admin panel
    page.goto(adminURL.format(category_id=categoryId, store_id=1))
    page.wait_for_selector("input#username")
    page.fill("input#username", CREDENTIALS["username"])
    page.fill("input#login", CREDENTIALS["password"])
    page.click("button.action-login")

    page.wait_for_load_state("networkidle")

    # Get store views IDs
    page.goto(divisionURL.format(category_id=categoryId, store_id=1))
    page.wait_for_load_state("networkidle")
    storeviews = page.locator(".store-switcher ul.dropdown-menu li.store-switcher-store-view a").evaluate_all(
        "elements => Object.fromEntries(elements.filter(el => el.getAttribute('data-value') !== null).map(el => [el.getAttribute('data-value'), el.textContent.trim()]))"
    )
    print ("Storeview IDs found")

    # Get default block value from the category URL without store
    defaultCategoryURL = divisionURL.replace('/store/{store_id}/', '/').format(category_id=categoryId)
    defaultValue = getDefaultValue(page, defaultCategoryURL)
    print(f"Default value: {defaultValue}")

    for id, storeview in storeviews.items():
        page.goto(divisionURL.format(category_id=categoryId, store_id=id))

        contentSection = page.locator(".fieldset-wrapper.admin__collapsible-block-wrapper:has(span:text('Content'))")
        try:
            contentSection.wait_for(state="visible", timeout=6000)
        except Exception:
            print(f"ID: {id} - Content not found, skipping")
            continue
        contentSection.click()

        selectLocator = page.locator(
            ".fieldset-wrapper.admin__collapsible-block-wrapper:has(span:text('Content')) "
            ".admin__field:last-child select"
        )
        try:
            selectLocator.wait_for(state="visible", timeout=6000)
        except Exception:
            print(f"ID: {id} - Select not found, skipping")
            continue
        selectedValue = selectLocator.evaluate("el => el.options[el.selectedIndex]?.text ?? el.value")

        # Check if "Use Default Value" checkbox for landing_page is checked
        checkboxLocator = page.locator(
            ".fieldset-wrapper.admin__collapsible-block-wrapper:has(span:text('Content')) "
            "input.admin__control-checkbox[name='use_default[landing_page]']"
        )
        isDefault = any(checkboxLocator.nth(i).is_checked() for i in range(checkboxLocator.count()))
        if isDefault:
            selectedValue = defaultValue
            print(f"ID: {id} ({storeview}) - {selectedValue} [D]")
        else:
            print(f"ID: {id} ({storeview}) - {selectedValue}")

        if selectedValue in EMPTY_CLP_VALUES:
            print(f"ID: {id} ({storeview}) - Empty value, skipping")
            continue

        if selectedValue not in blocks:
            blocksDetail[selectedValue] = [storeview]
            blocks.append(selectedValue)
        else:
            blocksDetail[selectedValue].append(storeview)

    browser.close()

print("Blocks found:", blocks)
for block, storeviews in blocksDetail.items():
    print(f"Block: {block} - Storeviews: {', '.join(storeviews)}")

elapsed = time.time() - startTime
print(f"Task done in: {elapsed:.2f} seconds")

# TODO Cuando una CLP tiene valor por defecto
#     - tiene checked <input type="checkbox" class="admin__control-checkbox" data-bind="attr: {id: $data.uid + '_default',name: 'use_default[' + $data.index + ']',}, checked: isUseDefault, disable: $data.serviceDisabled" id="QNGSOXF_default" name="use_default[description]">
#     - etiqueta o label <label class="admin__field-label" data-bind="attr: {for: $data.uid + '_default'}, i18n: 'Use Default Value'" for="QNGSOXF_default">Use Default Value</label>
#     - coger el valor de la store view default store view
