from fastapi import FastAPI, Request
from app.routers.auth import router as auth_router
from app.routers.api_key import router as api_key_router
from app.services.write_request_log import write_request_log
from starlette.background import BackgroundTask
import time

app = FastAPI()

# Production logger by default
app.state.request_log_writer = write_request_log

app = FastAPI()

app.state.write_request_log = True


@app.middleware("http")
async def log_request_middleware(request: Request, call_next):
    start = time.perf_counter()

    response = await call_next(request)

    total_time = time.perf_counter() - start

    if request.url.path != "/demo":
        return response

    if total_time * 1000 > 100:
        print(f"TOTAL REQUEST TIME: {total_time * 1000:.2f} ms")

    if app.state.write_request_log:
        user_id = getattr(request.state, "user_id", None)
        api_key_id = getattr(request.state, "api_key_id", None)

        response.background = BackgroundTask(
            write_request_log,
            user_id,
            api_key_id,
            response.status_code
        )

    return response

@app.get("/")
def hello():
    return "Hello"


app.include_router(auth_router)
app.include_router(api_key_router)