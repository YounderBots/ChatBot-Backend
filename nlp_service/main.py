from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from routes import router
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI(title="NLP Service", version="00.1", root_path="")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.add_middleware(SessionMiddleware, secret_key="some-random-string")


@app.get("/")
def root_api():
    """
    Root endpoint for NLP Service.
    Authentication not required.
    """
    return JSONResponse({"message": "Welcome to NLP Service"})


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
