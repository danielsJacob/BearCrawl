# Bearcrawl

## Build a standalone Windows executable

The build script downloads Playwright's Chromium browser and packages it with
the Playwright Python package. The target computer does not need Python,
Playwright, or a separately installed browser.

On a Windows build machine with [uv](https://docs.astral.sh/uv/) installed, run
from the project directory:

```powershell
.\build.ps1
```

The result is the `dist\Bearcrawl` folder. Distribute the whole folder
together; it contains `Bearcrawl.exe` and the bundled Playwright/Chromium
files. Build separately on each target operating system and architecture.
This folder-based build starts faster than a one-file executable because it
doesn't unpack the browser on each launch.

The application is packaged from `src\bearcrawl\`. Run it with
`uv run bearcrawl`; the Windows build script uses the package's `__main__.py`
as its entry point.

The application creates or reads `%USERPROFILE%\Documents\bearcrawl\config.json`.
The preferred-size setting is used for products with a size option. For
products without a size option, the app selects the first available variant.
Checkout Playwright actions use a 30-minute timeout. When the checkout form is
ready, the browser stays open for you to complete checkout manually; the app
does not click Pay now. Press Enter in the app console when you are finished.
If a checkout action times out, the browser stays open for manual review and
the cart is not cleared.