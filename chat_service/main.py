from configs import Configuration
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from fastapi.staticfiles import StaticFiles
from routes import router
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI(title="Chat Service", version="00.1", root_path="/hms")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["POST", "GET", "OPTIONS"],
    allow_headers=["*"],
)

app.add_middleware(SessionMiddleware, secret_key="some-random-string")

app.mount("/templates/static", StaticFiles(directory="templates/static"), name="static")


@app.on_event("startup")
def startup() -> None:
    """
    Application startup hook.
    Verifies database connectivity.
    """
    db = Configuration.SessionLocal()
    try:
        db.execute(text("SELECT 1"))  # Explicitly wrap the query in text()

    except SQLAlchemyError as e:
        print("Database connection failed", e)
    finally:
        db.close()


@app.get("/")
def root_api():
    """
    Root endpoint for Chat Service.
    Authentication not required.
    """
    return JSONResponse({"message": "Welcome to Chat Service"})


app.include_router(router)

my_routers = app.router.routes

all_urls = []


@app.get("/{path:path}")
def catch_all(path: str):
    """
    Define a catch-all route that will match any path not explicitly defined
    """
    if path not in all_urls:
        return JSONResponse({"message": "404 Not Found"})


for route in app.routes:
    if isinstance(route, APIRoute):
        all_urls.append(route.path)
