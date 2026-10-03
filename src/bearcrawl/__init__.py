from .checkout import (
    get_cart,
    clear_cart,
    add_cart,
    run_checkout,
    editConfig,
    load_config,
)

from urllib.parse import urlsplit, urlunsplit

import random
import requests
import time


DEBUG = False

session = requests.Session()


def clean_product_url(url):
    parts = urlsplit(url)

    path = parts.path

    if not path.endswith(".js"):
        path += ".js"

    return urlunsplit((
        parts.scheme,
        parts.netloc,
        path,
        "",  # remove ?variant= etc.
        "",
    ))
    
    
def menu():
    print("1. Enter Url")
    print("2. Edit Config")
    print("3. Exit")

    choice = input("Choose an option: ").strip()

    match choice:
        case "1":
            return True

        case "2":
            editConfig()
            return menu()
        
        case "3":
            print("Exiting...")
            return False

        case _:
            print("Error reading input. Please try again.")
            return menu()


def main():
    if not menu():
        return

    if DEBUG:
        product = (
            "https://bearwalker.com/products/"
            "toon-dark-magician-open-edition-deck"
        )
    else:
        product = input(
            "Input Bear Walker product URL: "
        ).strip()

    product = clean_product_url(product)

    print("Running", product)

    variant = check_availability(product)

    if variant is None:
        return

    print("\nAdding to cart")

    added = add_cart(
        variant["id"],
        quantity=1,
    )

    if added is None:
        return

    print("\nShowing cart")

    cart = get_cart()

    if cart is None:
        return

    run_checkout()


def find_preferred_variant(data):
    variants = data.get("variants", [])
    available_variants = [
        variant for variant in variants if variant.get("available")
    ]

    if not available_variants:
        return None

    options = data.get("options")
    size_options = [
        option
        for option in options or []
        if isinstance(option, dict)
        and "size" in str(option.get("name", "")).casefold()
    ]

    if options is not None and not size_options:
        print("Product has no size option. Selecting first available variant.")
        return available_variants[0]

    config = load_config()
    preferred_size = config.get("preferred_size", "L").strip().upper()
    option_position = int(size_options[0].get("position", 1)) if size_options else 1
    option_key = f"option{option_position}"

    for variant in available_variants:
        size = str(variant.get(option_key, "")).strip().upper()

        if size == preferred_size:
            return variant

    return None

def check_availability(product_url):
    print("\nWatching:", product_url)

    while True:
        try:
            response = session.get(
                product_url,
                timeout=3,
            )

            # Respect actual rate-limit response
            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")

                if retry_after:
                    delay = float(retry_after)
                else:
                    delay = 5

                print(f"Rate limited. Waiting {delay:.1f}s...")
                time.sleep(delay)
                continue

            # Temporary server problem
            if response.status_code >= 500:
                print("Server error. Retrying shortly...")
                time.sleep(2)
                continue

            if not response.ok:
                print("Request failed:", response.status_code)
                time.sleep(2)
                continue

            data = response.json()

            variant = find_preferred_variant(data)

            if variant is not None:
                print("\nFOUND AVAILABLE VARIANT")
                print("Name:", variant["name"])
                print("Variant ID:", variant["id"])
                print("Inventory:", variant["inventory_quantity"])

                return variant

            # Fast normal polling
            delay = random.uniform(1.0, 1.8)

            print(
                f"No available matching variant. "
                f"Retrying in {delay:.2f}s..."
            )

            time.sleep(delay)

        except requests.Timeout:
            print("Request timed out. Retrying...")
            time.sleep(1)

        except requests.RequestException as error:
            print("Request error:", error)
            time.sleep(2)

        except KeyboardInterrupt:
            print("\nStopped.")
            return None