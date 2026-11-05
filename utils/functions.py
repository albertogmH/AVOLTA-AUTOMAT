"""Common helper functions shared across automation scripts."""

from time import monotonic
from urllib.parse import urlsplit


def login_magento_admin(page, admin_url, username, password, timeout=15000, on_failure=None):
    """Return True only for a trusted Magento admin shell; submit login at most once."""
    from playwright.sync_api import Error, TimeoutError as PlaywrightTimeoutError

    expected = urlsplit(admin_url)
    admin_path = expected.path.rstrip("/")
    if admin_path.endswith("/dashboard"):
        admin_path = admin_path[:-len("/dashboard")]
    deadline = monotonic() + timeout / 1000
    submitted = False
    state_script = """({origin, adminPath, submitted}) => {
        const visible = selector => [...document.querySelectorAll(selector)]
            .some(element => element.getClientRects().length &&
                getComputedStyle(element).visibility !== 'hidden');
        if (location.origin !== origin ||
            !(location.pathname === adminPath || location.pathname.startsWith(adminPath + '/')))
            return false;
        const login = visible('input#username');
        if (!login && (visible('.admin__menu') ||
            (visible('#nav') && visible('.page-wrapper .page-header .admin-user'))))
            return 'authenticated';
        if (submitted) {
            if (login && visible('.message-error, [data-ui-id="messages-message-error"], .admin__field-error'))
                return 'rejected';
        } else if (login && visible('input#login') && visible('button.action-login')) {
            return 'form';
        }
        return false;
    }"""

    def remaining():
        milliseconds = (deadline - monotonic()) * 1000
        if milliseconds <= 0:
            raise PlaywrightTimeoutError("Login deadline reached.")
        return milliseconds

    def fail(reason):
        if on_failure is not None:
            on_failure(reason)
        return False

    def trusted_location():
        actual = urlsplit(page.url)
        return (not actual.username and not actual.password
                and (actual.scheme, actual.netloc) == (expected.scheme, expected.netloc)
                and (actual.path == admin_path or actual.path.startswith(admin_path + "/")))

    try:
        page.goto(admin_url, wait_until="domcontentloaded", timeout=remaining())
        arguments = {"origin": f"{expected.scheme}://{expected.netloc}",
                     "adminPath": admin_path, "submitted": False}
        state = page.wait_for_function(state_script, arg=arguments, timeout=remaining())
        try:
            if state.json_value() == "authenticated":
                return trusted_location()
        finally:
            state.dispose()
        if not trusted_location():
            return fail("Magento login redirected outside the configured admin location.")
        page.fill("input#username", username, timeout=remaining())
        page.fill("input#login", password, timeout=remaining())
        if not trusted_location():
            return fail("Magento login redirected outside the configured admin location.")
        submitted = True
        page.click("button.action-login", timeout=remaining(), no_wait_after=True)
        arguments["submitted"] = True
        state = page.wait_for_function(state_script, arg=arguments, timeout=remaining())
        try:
            if state.json_value() == "authenticated" and trusted_location():
                return True
        finally:
            state.dispose()
        return fail("Magento login form reported a rejection; authentication was not confirmed.")
    except PlaywrightTimeoutError:
        try:
            if not trusted_location():
                return fail("Magento login redirected outside the configured admin location.")
            if page.locator("input#username").is_visible():
                return fail("Magento login timed out with the login form still visible; authentication was not confirmed.")
        except (Error, ValueError):
            pass
        stage = "after submission" if submitted else "before submission"
        return fail(f"Magento login timed out {stage} waiting for a confirmed admin shell.")
    except (Error, ValueError):
        return fail("Magento login browser/navigation failure; authentication was not confirmed.")
