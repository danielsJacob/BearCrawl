# Bearcrawl
## Build / Download

You have two options to use Bearcrawl on Windows:

### Option 1 — Download the latest release

The easiest option is to download the latest Windows release from the project's Releases page.

The release includes the packaged application, so the target computer does not need Python, Playwright, or a separately installed browser.

### Option 2 — Build from source

To build Bearcrawl yourself, you need Windows and uv installed.

From the project directory, run:

```powershell
.\build.ps1
```

The build script downloads Playwright's Chromium browser and packages it together with the Playwright Python package