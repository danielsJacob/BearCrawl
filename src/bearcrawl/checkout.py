from playwright.sync_api import (
    Playwright,
    TimeoutError as PlaywrightTimeoutError,
    sync_playwright,
)
import requests, time, random

BASE_URL = "https://bearwalker.com"
CHECKOUT_TIMEOUT_MS = 30 * 60 * 1000

session = requests.Session()


def run(playwright: Playwright, link: str):
    browser = playwright.chromium.launch(headless=True)

    context = browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/154.0.0.0 Safari/537.36"
        )
    )

    page = context.new_page()

    response = page.goto(link, wait_until="domcontentloaded")

    if response is None:
        print("No response received.")
        context.close()
        browser.close()
        return None

    print("Status Code:", response.status)

    if response.status == 429:
        print("Rate limited.")
        print("Retry-After:", response.headers.get("retry-after"))

        context.close()
        browser.close()
        return None

    if response.status != 200:
        print("Unexpected status:", response.status)

        context.close()
        browser.close()
        return None

    data = response.json()
    
    def choose_variant(data):
        config = load_config()

        preferred_size = config.get("preferred_size", "").strip().upper()
        fallback_size = "L"

        available_variants = [
            variant
            for variant in data["variants"]
            if variant["available"]
        ]

        if not available_variants:
            print("No available variants.")
            return None

        # 1. Try preferred size
        if preferred_size:
            for variant in available_variants:
                if variant["option1"].upper() == preferred_size:
                    print(f"Found preferred size: {preferred_size}")
                    return variant

        # 2. Fall back to Large
        for variant in available_variants:
            if variant["option1"].upper() == fallback_size:
                print(
                    f"Preferred size {preferred_size or 'not set'} unavailable. "
                    f"Falling back to {fallback_size}."
                )
                return variant

        # 3. Last resort: any available variant
        print("Preferred and fallback sizes unavailable.")
        print("Using first available variant.")

        return available_variants[0]

    variant = choose_variant(data)

    if variant is None:
        context.close()
        browser.close()
        return None

    product_data = {
        "product_id": data["id"],
        "variant_id": variant["id"],
        "name": variant["name"],
        "available": variant["available"],
        "price": variant["price"],
        "weight": variant["weight"],
        "inventory_quantity": variant["inventory_quantity"],
        "image": data["featured_image"],
        "url": data["url"],
    }

    print("Variant ID:", product_data["variant_id"])
    print("Name:", product_data["name"])
    print("Available:", product_data["available"])
    print(f"Price: ${product_data['price'] / 100:.2f}")
    print("Weight:", product_data["weight"])
    print("Inventory:", product_data["inventory_quantity"])
    print("Image:", product_data["image"])
    print("URL:", product_data["url"])

    context.close()
    browser.close()

    return product_data


def run_site(link: str):
    with sync_playwright() as playwright:
        return run(playwright, link)


def add_cart(variant_id: int, quantity: int = 1):
    max_attempts = 3

    for attempt in range(max_attempts):
        response = session.post(
            f"{BASE_URL}/cart/add.js",
            data={
                "id": variant_id,
                "quantity": quantity,
            },
        )

        print("Add status:", response.status_code)

        if response.ok:
            item = response.json()

            print("Added:", item["title"])

            return item

        if response.status_code != 429:
            print("Add failed:", response.text)

            return None

        retry_after = response.headers.get("Retry-After")

        if retry_after:
            delay = float(retry_after)
        else:
            delay = (2**attempt) * 5 + random.uniform(0, 1)

        print(f"Rate limited. Delaying retry " f"by about {delay:.1f}s")

        time.sleep(delay)

    print("Still rate limited after retries.")

    return None


def get_cart():
    response = session.get(f"{BASE_URL}/cart.js")

    print("Cart status:", response.status_code)

    if response.status_code == 429:
        print("Rate limited while getting cart.")
        print("Retry-After:", response.headers.get("Retry-After"))

        return None

    if not response.ok:
        print("Cart failed:", response.text)

        return None

    cart = response.json()

    print("Items:", cart["item_count"])

    print(f"Total: " f"${cart['total_price'] / 100:.2f}")

    for item in cart["items"]:
        print(item["title"], "x", item["quantity"], f"${item['line_price'] / 100:.2f}")

    return cart


def clear_cart():
    response = session.post(f"{BASE_URL}/cart/clear.js")

    print("Clear status:", response.status_code)

    if response.status_code == 429:
        print("Rate limited while clearing cart.")
        print("Retry-After:", response.headers.get("Retry-After"))

        return None

    if not response.ok:
        print("Clear failed:", response.text)

        return None

    cart = response.json()

    print("Cart cleared")

    print("Items:", cart["item_count"])

    print(f"Total: " f"${cart['total_price'] / 100:.2f}")

    return cart


def copy_session_cookies_to_context(session, context):
    playwright_cookies = []

    for cookie in session.cookies:
        playwright_cookies.append(
            {
                "name": cookie.name,
                "value": cookie.value,
                "domain": cookie.domain,
                "path": cookie.path or "/",
                "secure": cookie.secure,
            }
        )

    context.add_cookies(playwright_cookies)


def checkout(playwright: Playwright):
    browser = playwright.chromium.launch(headless=False)

    context = browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/154.0.0.0 Safari/537.36"
        )
    )

    timed_out = False
    page = None
    try:
        copy_session_cookies_to_context(session, context)

        page = context.new_page()
        page.set_default_timeout(CHECKOUT_TIMEOUT_MS)
        page.set_default_navigation_timeout(CHECKOUT_TIMEOUT_MS)

        response = page.goto(f"{BASE_URL}/checkout", wait_until="domcontentloaded")

        if response:
            print("Checkout status:", response.status)

        print("Checkout URL:", page.url)

        fill_checkout(page)

        print("Checkout ready.")

    except PlaywrightTimeoutError as error:
        timed_out = True
        print(f"Checkout timed out: {error}")
        print("The checkout browser will remain open for manual review.")
        input("Press Enter in this console when you are finished...")

    finally:
        if not timed_out:
            clear_cart()
        context.close()
        browser.close()
        


def run_checkout():
    with sync_playwright() as playwright:
        checkout(playwright)


def fill_checkout(page):
    config = load_config()

    page.get_by_role("textbox", name="Email").fill(config["email"])

    page.get_by_role("textbox", name="First name", exact=True).fill(
        config["first_name"]
    )

    page.get_by_role("textbox", name="Last name", exact=True).fill(config["last_name"])

    page.get_by_role("combobox", name="Address").fill(config["address1"])

    if config["address2"]:
        page.get_by_role("textbox", name="Apartment, suite, etc. (optional)").fill(
            config["address2"]
        )

    page.get_by_role("textbox", name="City").fill(config["city"])

    page.get_by_role("combobox", name="State").select_option(config["state"])

    page.get_by_role("textbox", name="ZIP code").fill(config["zip"])

    page.get_by_role("textbox", name="Phone").fill(config["phone"])

    # Shopify PCI payment iframes

    page.frame_locator('iframe[title="Card number"]').locator(
        'input[name="number"]'
    ).fill(config["card_number"])

    page.frame_locator('iframe[title="Expiration date (MM / YY)"]').locator(
        'input[name="expiry"]'
    ).fill(config["expiration_date"])

    page.frame_locator('iframe[title="Security code"]').locator(
        'input[name="verification_value"]'
    ).fill(config["security_code"])

    page.frame_locator('iframe[title="Name on card"]').locator(
        'input[name="name"]'
    ).fill(config["card_name"])
    pay_now = page.get_by_role("button", name="Pay now")
    pay_now.wait_for(state="visible")
    print("Checkout is ready. Pay now will not be clicked automatically.")
    input("Complete checkout manually, then press Enter here to close...")


import json, os, os
from pathlib import Path

CONFIG_DIR = Path.home() / "Documents" / "bearcrawl"
CONFIG_FILE = CONFIG_DIR / "config.json"
DEFAULT_CONFIG = {
    "preferred_size": "L",
    "email": "",
    "first_name": "",
    "last_name": "",
    "address1": "",
    "address2": "",
    "city": "",
    "state": "",
    "zip": "",
    "phone": "",
    "card_number": "",
    "expiration_date": "",
    "security_code": "",
    "card_name": "",
    "auto_pay": False,
}
CONFIG_FIELDS = {
    "preferred_size": "Preferred Size |S|M||L||XL|XL|XXL|",
    "email": "Email",
    "first_name": "First Name",
    "last_name": "Last Name",
    "address1": "Address",
    "address2": "Address Line 2",
    "city": "City",
    "state": "State",
    "zip": "ZIP Code",
    "phone": "Phone",
    #"card_number": "Card number",
    #"expiration_date": "Expiration date (MM / YY)",
    #"security_code": "Security code",
    #"card_name": "Name on Card",
    #"auto_pay": "Auto Pay",
}


def load_config():
    config = DEFAULT_CONFIG.copy()
    if not CONFIG_FILE.exists():
        return config

    with CONFIG_FILE.open("r", encoding="utf-8") as file:
        saved_config = json.load(file)

    config.update(saved_config)

    return config


def save_config(config):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with CONFIG_FILE.open("w", encoding="utf-8") as file:
        json.dump(config, file, indent=4)


def editConfig():
    config = load_config()

    print(f"\nEditing config: {CONFIG_FILE}")
    print("Press Enter to keep the current value.\n")

    for key, label in CONFIG_FIELDS.items():
        current = config[key]

        if key == "preferred_size":
            print(f"{label} [{current}]")
            value = input("Enter preferred size: ").strip().upper()

            if value:
                if value in ("S", "M", "L", "XL", "XXL"):
                    config[key] = value
                else:
                    print("Invalid size. Keeping current setting.")

        elif key == "auto_pay":
            value = input(
                f"{label} [{current}] (true/false): "
            ).strip().lower()

            if value:
                if value in ("true", "yes", "y", "1"):
                    config[key] = True
                elif value in ("false", "no", "n", "0"):
                    config[key] = False
                else:
                    print("Invalid value. Keeping current setting.")

        else:
            value = input(f"{label} [{current}]: ").strip()

            if value:
                config[key] = value

    save_config(config)

    print(f"\nSaved config: {CONFIG_FILE}")