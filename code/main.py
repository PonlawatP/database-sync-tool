from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import uvicorn
from typing import Dict
from sync.db_sync import sync_databases, fake_sync, sync_status, update_sync_status
import asyncio
from contextlib import asynccontextmanager
from fastapi.responses import RedirectResponse, FileResponse

current_task = None  # Track the current sync task

async def runner():
    global sync_status, running, current_task
    
    while True:
        if running:
            running = False
            try:
                # Create a task that can be cancelled
                current_task = asyncio.create_task(sync_databases())
                await current_task
                sync_status.update({
                    "is_running": False,
                    "last_status": "success",
                    "current_operation": None,
                    "last_sync": datetime.now().isoformat()
                })
            except asyncio.CancelledError:
                # Handle the cancellation
                sync_status.update({
                    "is_running": False,
                    "last_status": "cancelled",
                    "current_operation": None
                })
            except Exception as e:
                print(f"Sync error: {e}")
                sync_status.update({
                    "is_running": False,
                    "last_status": "error",
                    "current_operation": None
                })
            finally:
                current_task = None
        await asyncio.sleep(1)

async def main():
    config = uvicorn.Config(app, host="0.0.0.0", port=8000)
    server = uvicorn.Server(config)
    await asyncio.gather(
        server.serve(),
        runner()
    )

@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(runner())
    yield
    print("Shutting down...")

app = FastAPI(lifespan=lifespan)

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Add routes
@app.get("/")
async def root():
    return FileResponse("static/index.html")

# Initialize scheduler
def run_sync():
    global running, sync_status
    sync_status["is_running"] = True
    sync_status["current_operation"] = "Starting sync process"
    
    running = True

scheduler = BackgroundScheduler()
scheduler.add_job(run_sync, 'cron', hour=0, minute=0)
scheduler.start()

@app.get("/sync/status")
async def get_sync_status():
    import logging
    logging.getLogger('uvicorn.access').disabled = True
    return sync_status

running = False
@app.post("/sync")
async def trigger_sync():
    global sync_status, running
    import logging
    logging.getLogger('uvicorn.access').disabled = False
    
    if sync_status["is_running"]:
        raise HTTPException(status_code=400, detail="Sync is already running")
    
    try:
        sync_status["is_running"] = True
        sync_status["current_operation"] = "Starting sync process"
        
        running = True

        return {
            "status": "success",
            "message": f"Sync completed at {sync_status['last_sync']}"
        }
    except Exception as e:
        sync_status.update({
            "is_running": False,
            "last_status": "error",
            "current_operation": None
        })
        raise HTTPException(status_code=500, detail=str(e))
    

@app.post("/sync/stop")
async def stop_sync():
    global sync_status, current_task
    import logging
    logging.getLogger('uvicorn.access').disabled = False
    if not sync_status["is_running"]:
        raise HTTPException(status_code=400, detail="No sync process is running")
    
    # Cancel the current sync task if it exists
    if current_task:
        current_task.cancel()
    
    sync_status.update({
        "is_running": False,
        "current_operation": None,
        "last_status": "cancelled"
    })
    
    return {"status": "success", "message": "Sync process stopped"}


if __name__ == "__main__":
    print("Application entry point")  # Debug log
    asyncio.run(main())
    