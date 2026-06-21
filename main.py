import asyncio
import random
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup  # Still for proxy scraping

TARGET_URL = "https://shy.bio/67"

@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(continuous_browser_hammer())
    yield

app = FastAPI(title="Browser Auto-Hammer - shy.bio/67", lifespan=lifespan)

async def scrape_open_proxies() -> list:
    proxies = []
    sources = ["https://www.sslproxies.org/", "https://free-proxy-list.net/", "https://www.us-proxy.org/"]
    async with async_playwright() as p:  # Reuse for scraping if wanted, but simple aiohttp fallback omitted for brevity
        # ... (keep similar scraping logic, or simplify)
        pass  # Implement as before or extend
    # Placeholder - fill with your previous scrape logic returning http://ip:port
    return ["http://example-proxy:8080"] * 50  # Replace with real scrape

async def browser_hammer_cycle():
    proxies = await scrape_open_proxies()
    if not proxies:
        await asyncio.sleep(30)
        return

    async with async_playwright() as p:
        for proxy_str in proxies:
            try:
                proxy_config = {"server": proxy_str}
                browser = await p.chromium.launch(
                    headless=True,
                    proxy=proxy_config,
                    args=['--no-sandbox', '--disable-setuid-sandbox']
                )
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36'
                )
                page = await context.new_page()
                
                # Navigate and wait for full load
                await page.goto(TARGET_URL, wait_until='networkidle', timeout=45000)
                await page.wait_for_load_state('domcontentloaded')
                await asyncio.sleep(random.uniform(2, 5))  # Human-like pause
                
                # Click once: example on first prominent button/link; customize selector for shy.bio/67
                try:
                    await page.locator('button, a, [role="button"]').first.click(timeout=10000)
                    print(f"Clicked on {TARGET_URL} via {proxy_str}")
                    await asyncio.sleep(random.uniform(1.5, 3.5))  # Post-click dwell
                except:
                    print(f"No clickable element or click failed via {proxy_str}")
                
                await browser.close()
                print(f"Cycle complete for proxy {proxy_str} @ {time.strftime('%H:%M:%S')}")
                await asyncio.sleep(random.uniform(0.5, 2.0))
            except Exception as e:
                print(f"Browser cycle failed for {proxy_str}: {str(e)[:100]}")
                continue

async def continuous_browser_hammer():
    while True:
        print(f"New browser hammer cycle on {TARGET_URL}")
        await browser_hammer_cycle()
        await asyncio.sleep(15)  # Cooldown between full proxy sweeps

@app.get("/health")
async def health():
    return {"status": "Browser-based auto-hammer running on https://shy.bio/67"}

# Manual trigger remains
@app.post("/start-spam")
async def manual_trigger(background_tasks: BackgroundTasks):
    background_tasks.add_task(browser_hammer_cycle)
    return JSONResponse({"status": "Manual browser hammer cycle triggered"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
