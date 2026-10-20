"""Administrator-only manual ingestion trigger using the normal coordinated worker."""
from fastapi import APIRouter, BackgroundTasks, Depends

from app.dependencies import require_admin
from app.workers.quarterly_results_worker import poll_once

router = APIRouter(tags=["ingestion"], dependencies=[Depends(require_admin)])


@router.post("/trigger-ingestion", status_code=202)
async def trigger_ingestion(background_tasks: BackgroundTasks):
    background_tasks.add_task(poll_once, dispose_engine=False)
    return {"status": "SCHEDULED", "message": "Quarterly ingestion scheduled. Read /api/results/latest for the completed worker status.",
            "status_url": "/api/results/latest"}
