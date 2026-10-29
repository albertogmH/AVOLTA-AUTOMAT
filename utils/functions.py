"""Common helper functions shared across automation scripts."""


def login_magento_admin(page, admin_url, username, password, timeout=15000):
    """Logs into a Magento admin panel. Returns True if the login form disappears after submit."""
    page.goto(admin_url, wait_until="domcontentloaded")
    try:
        page.wait_for_selector("input#username", timeout=timeout)
    except Exception:
        return False

    page.fill("input#username", username)
    page.fill("input#login", password)
    page.click("button.action-login")
    page.wait_for_load_state("networkidle")

    return page.locator("input#username").count() == 0
