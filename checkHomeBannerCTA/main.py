import sys
import os
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
try:
    from urllib3.exceptions import NotOpenSSLWarning
    warnings.filterwarnings("ignore", category=NotOpenSSLWarning)
except ImportError:
    pass
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import time
from playwright.sync_api import sync_playwright
from utils.config import APP_CREDENTIALS, APP_PROD_URL, APP_STAGING_URL, APP_PROD_HOMEID, APP_STAGING_HOMEID, APP_DEFAULT_LANGUAGE, APP_LANGUAGES
from deep_translator import GoogleTranslator

ENVIRONMENTS = {
    "PROD": {
        "url": APP_PROD_URL,
        "home_id": APP_PROD_HOMEID,
    },
    "STG": {
        "url": APP_STAGING_URL,
        "home_id": APP_STAGING_HOMEID,
    },
}

# Mapping from Umbraco culture codes to Google Translate language codes
TRANSLATE_LANG_MAP = {
    'ar': 'ar',    
    'zh': 'zh-CN', 
    'zh-HK': 'zh-TW', 
    'zh-CN': 'zh-CN',
    'da': 'da',    
    'fi-FI': 'fi', 
    'fr': 'fr',        
    'de': 'de',
    'el': 'el',    
    'id': 'id',    
    'it-IT': 'it',     
    'ko': 'ko',
    'ms': 'ms',    
    'no': 'no',    
    'pt-BR': 'pt',     
    'ru': 'ru',
    'es': 'es',    
    'sv-SE': 'sv', 
    'th-TH': 'th',     
    'tr-TR': 'tr',
    'vi': 'vi',
}

def back_translate_batch(items, lang_code):
    google_lang = TRANSLATE_LANG_MAP.get(lang_code, lang_code.split('-')[0])
    translations = [""] * len(items)
    to_translate = [(i, text) for i, text in enumerate(items)
                    if text not in ("[Empty]", "[Missing]", "")]
    if not to_translate:
        return translations
    try:
        translator = GoogleTranslator(source=google_lang, target='en')
        texts = [t for _, t in to_translate]
        translated_texts = translator.translate_batch(texts)
        for (i, _), translated in zip(to_translate, translated_texts):
            translations[i] = translated or ""
    except Exception as e:
        print(f"\n  [Translation error for {lang_code}: {e}]")
    return translations


def login_umbraco(page, environment):
    target = ENVIRONMENTS[environment]
    print(f"Navigating to {environment}: {target['url']}")
    page.goto(target["url"], wait_until="domcontentloaded")
    page.wait_for_load_state("networkidle")

    # Wait for login form to be visible
    email_input = page.locator("input#email")
    try:
        email_input.wait_for(state="visible", timeout=15000)
    except Exception:
        print("Email field not found, continuing...")
        return target

    password_input = page.locator("input#password")
    sign_in_button = page.locator("button#next")

    print("Filling in credentials...")
    email_input.fill(APP_CREDENTIALS["username"])
    password_input.fill(APP_CREDENTIALS["password"])
    sign_in_button.click()

    # Wait for login to complete
    try:
        page.wait_for_url("**/umbraco#/**", timeout=30000)
        print("Login completed successfully")
    except Exception:
        print("Waiting for page to load...")
        page.wait_for_load_state("networkidle")

    return target

def extract_cta_banner_items(page, verbose=True):
    try:
        page.wait_for_load_state("networkidle")

        # Wait for the CTA Banner V2 label to appear in the DOM.
        # state=attached is more permissive than visible and won't fail if the element is off-screen or hidden.
        page.wait_for_selector(
            "label.control-label[data-element='property-label-callToActionBannerV2']",
            state="attached",
            timeout=30000
        )

        # Locate the CTA Banner V2 label list
        cta_wrap = page.locator("div.umb-el-wrap").filter(
            has=page.locator(
                "div.control-header > label.control-label[data-element='property-label-callToActionBannerV2']"
            )
        ).first

        # Wait for the list of items to load
        buttons_locator = cta_wrap.locator(
            "div.umb-block-list__block--view button.blockelement-labelblock-editor"
        )
        buttons_locator.first.wait_for(state="attached", timeout=30000)

        if verbose:
            print("'Call To Action Banner V2' container found")

        # Extract titles using JS
        buttons_locator = cta_wrap.locator(
            "div.umb-block-list__block--view button.blockelement-labelblock-editor"
        )

        titles = buttons_locator.evaluate_all(
            """buttons => buttons.map(btn => {
                const spans = Array.from(btn.querySelectorAll(':scope > span'));
                const titleSpan = spans[spans.length - 1];
                return titleSpan ? titleSpan.textContent.trim() : '';
            })"""
        )

        items = []
        if verbose:
            print(f"Total items found: {len(titles)}")

        for i, text in enumerate(titles):
            if text:
                items.append(text)
                if verbose:
                    print(f"{i+1}. {text}")
            else:
                items.append("[Empty]")
                if verbose:
                    print(f"{i+1}. [Empty]")

        return items

    except Exception as e:
        print(f"Error extracting items: {str(e)}")
        return []

# Request all inputs upfront
environment = input("Type PROD or STG: ").strip().upper()
while environment not in ENVIRONMENTS:
    environment = input("Invalid environment. Type PROD or STG: ").strip().upper()

do_translate = input("Add back-translation to report? (y/n): ").strip().lower() == "y"
save = input("Save report to file? (y/n): ").strip().lower()

startTime = time.time()

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()

    target_info = login_umbraco(page, environment)
    print(f"Logged in to {environment} | HOME_ID: {target_info['home_id']}")

    base_url = f"{target_info['url']}/content/edit/{target_info['home_id']}"

    # Extract default language
    print(f"\n--- Extracting default language ({APP_DEFAULT_LANGUAGE}) ---")
    page.goto(f"{base_url}?mculture={APP_DEFAULT_LANGUAGE}", wait_until="domcontentloaded")
    default_items = extract_cta_banner_items(page, verbose=True)
    print(f"Total items in default ({APP_DEFAULT_LANGUAGE}): {len(default_items)}")

    # Extract all other languages
    results = {}
    for lang in APP_LANGUAGES:
        print(f"\n[{lang}] Extracting...")
        page.goto(f"{base_url}?mculture={APP_DEFAULT_LANGUAGE}&cculture={lang}", wait_until="domcontentloaded")
        results[lang] = extract_cta_banner_items(page, verbose=False)
        print(f"[{lang}] {len(results[lang])} items found")

    back_translations = {}
    if do_translate:
        print("Translating items to English...")
        for lang in APP_LANGUAGES:
            print(f"  [{lang}]...", end=" ", flush=True)
            back_translations[lang] = back_translate_batch(results[lang], lang)
            print("done")

    # Build report
    separator = "=" * 60
    default_count = len(default_items)
    report_lines = [
        separator,
        "TRANSLATION REPORT - Call To Action Banner V2",
        separator,
        f"Reference: {APP_DEFAULT_LANGUAGE} ({default_count} banners)",
    ]

    # Summary of languages with problems (banner count mismatch)
    summary_lines = []
    for lang in APP_LANGUAGES:
        lang_count = len(results[lang])
        if lang_count != default_count:
            summary_lines.append(f"{lang} > Banners: {lang_count}/{default_count}")

    report_lines.append(f"\n--- SUMMARY ---")
    if summary_lines:
        report_lines.extend(summary_lines)
    else:
        report_lines.append("No problems found (all languages complete)")

    for lang in APP_LANGUAGES:
        lang_items = results[lang]
        lang_count = len(lang_items)
        diff = lang_count - default_count

        report_lines.append(f"\n--- {lang} ---")
        if diff < 0:
            report_lines.append(f"Banners: {lang_count}/{default_count} ({abs(diff)} missing)")
        elif diff > 0:
            report_lines.append(f"Banners: {lang_count}/{default_count} ({diff} extra)")
        else:
            report_lines.append(f"Banners: {lang_count}/{default_count} (complete)")

        max_rows = max(default_count, lang_count)
        for i in range(max_rows):
            default_text = default_items[i] if i < default_count else "[Missing]"
            lang_text = lang_items[i] if i < lang_count else "[Missing]"
            suffix = ""
            if do_translate and lang_text not in ("[Empty]", "[Missing]"):
                bt_list = back_translations.get(lang, [])
                bt_text = bt_list[i] if i < len(bt_list) else ""
                if bt_text and bt_text.lower() != default_text.lower():
                    suffix = f" [{bt_text}]"
            report_lines.append(f"{i+1}. {default_text} - {lang_text}{suffix}")

    report_lines.append(f"\n{separator}")

    # Print report
    for line in report_lines:
        print(line)

    if save == "y":
        report_path = os.path.join(os.path.dirname(__file__), f"report_{environment}.txt")
        with open(report_path, "w", encoding="utf-8") as f:
            f.write("\n".join(report_lines))
        print(f"Report saved to: {report_path}")

    browser.close()

elapsed = time.time() - startTime
print(f"Task completed in: {elapsed:.2f} seconds")