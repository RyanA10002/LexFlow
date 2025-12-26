"""
Celery tasks: enqueue cell execution and return results.
"""
import os
from celery import Celery
from celery.result import AsyncResult
from backend.sandbox_runner import SandboxRunner

CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL", "redis://localhost:6379/0")
app = Celery("backend.tasks", broker=CELERY_BROKER_URL, backend=CELERY_BROKER_URL)

runner = SandboxRunner()

@app.task(bind=True)
def run_cell_async(self, payload):
    try:
        out = runner.execute_in_sandbox(payload, task_id=self.request.id, timeout=30)
        return {"status": "success", "output": out}
    except Exception as e:
        return {"status": "error", "error": str(e)}

def get_task_result(task_id: str):
    ar = AsyncResult(task_id, app=app)
    if not ar:
        return None
    if ar.ready():
        return {"ready": True, "result": ar.result}
    else:
        return {"ready": False}
