import asyncio
import random
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import JSONResponse
from playwright.async_api import async_playwright, Error
import aiohttp
from bs4 import BeautifulSoup

TARGET_URL = "https://shy.bio/67"

@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(continuous_browser_hammer())
    yield

app = FastAPI(title="Robust Browser Hammer shy.bio/67", lifespan=lifespan)

async def scrape_open_proxies() -> list:
    proxies = []
    sources = ["https://www.sslproxies.org/", "https://free-proxy-list.net/"]
    headers = {'User-Agent': 'Mozilla/5.0'}
    async with aiohttp.ClientSession(headers=headers) as session:
        for url in sources:
            try:
                async with session.get(url, timeout=20) as resp:
                    if resp.status == 200:
                        soup = BeautifulSoup(await resp.text(), 'html.parser')
                        table = soup.find('table')
                        if table:
                            for row in table.find_all('tr')[1:120]:
                                cols = row.find_all('td')
                                if len(cols) >= 2:
                                    ip = cols[0].text.strip()
                                    port = cols[1].text.strip()
                                    if ip and port and '.' in ip:
                                        proxies.append(f"http://{ip}:{port}")
            except:
                continue
    proxies = list(set(proxies))
    random.shuffle(proxies)
    return proxies[:300]

async def attempt_browser_visit(proxy_str: str):
    try:
        async with async_playwright() as p:
            proxy_config = {"server": proxy_str}
            browser = await p.chromium.launch(
                headless=True,
                proxy=proxy_config,
                args=[
                    '--no-sandbox', '--disable-setuid-sandbox', 
                    '--disable-dev-shm-usage', '--disable-gpu',
                    '--single-process', '--no-zygote'
                ]
            )
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent=random.choice([
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                ])
            )
            page = await context.new_page()
            
            await page.goto(TARGET_URL, wait_until='networkidle', timeout=60000)
            await page.wait_for_load_state('domcontentloaded')
            await asyncio.sleep(random.uniform(2, 5))
            
            try:
                await page.locator('button, a, text=/click to enter/i, [role="button"]').first.click(timeout=20000)
                print(f"✅ SUCCESS Click on {TARGET_URL} via {proxy_str}")
            except:
                print(f"Click skipped/fallback on {proxy_str}")
            
            await browser.close()
            return True
    except Exception as e:
        print(f"Browser fail {proxy_str}: {str(e)[:150]}")
        return False

async def browser_hammer_cycle():
    proxies = await scrape_open_proxies()
    if not proxies:
        print("No proxies - sleeping...")
        await asyncio.sleep(45)
        return

    for proxy_str in proxies:
        success = await attempt_browser_visit(proxy_str)
        if not success:
            # Lightweight HTTP fallback for dead proxies
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(TARGET_URL, proxy=proxy_str, timeout=15) as resp:
                        print(f"HTTP fallback {proxy_str} -> {resp.status}")
            except:
                pass
        await asyncio.sleep(random.uniform(1.5, 4))

async def continuous_browser_hammer():
    while True:
        print(f"🚀 New hammer cycle on {TARGET_URL} - {time.strftime('%H:%M:%S')}")
        await browser_hammer_cycle()
        await asyncio.sleep(25)

@app.get("/health")
async def health():
    return {"status": "Auto hammer active - check logs for clicks"}

@app.post("/start-spam")
async def manual_trigger(background_tasks: BackgroundTasks):
    background_tasks.add_task(browser_hammer_cycle)
    return JSONResponse({"status": "Manual cycle queued"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
