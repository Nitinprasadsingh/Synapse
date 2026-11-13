import asyncio
import httpx
from app.main import app

async def run():
    print("Creating transport...")
    transport = httpx.ASGITransport(app=app)
    print("Entering AsyncClient...")
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        print("Sending GET...")
        res = await client.get("/api/v1/system/health")
        print("Response:", res.status_code, res.json())

if __name__ == "__main__":
    asyncio.run(run())
