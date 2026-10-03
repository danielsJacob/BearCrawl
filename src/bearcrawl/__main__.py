import os
import sys

if getattr(sys, "frozen", False):
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = os.path.join(
        sys._MEIPASS,
        "playwright-browsers",
    )

from bearcrawl import main

if __name__ == "__main__":
    main()
