
import asyncio
from playwright.async_api import async_playwright
async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://example.com", timeout=15000)
        text = await page.inner_text("body")
        print(text[:3000])
        await browser.close()
asyncio.run(main())
