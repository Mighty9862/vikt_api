import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi
from presentation import router as ApiV2Router
import uvicorn

app = FastAPI(
    title="Vikt API",
    docs_url=None,
    redoc_url=None,
    openapi_url="/api/openapi.json"
)

relative_path = "static/images/"
absolute_path = os.path.abspath(relative_path)

static_dir = "static"
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

images_dir = os.path.join(static_dir, "images")
if not os.path.exists(images_dir):
    os.makedirs(images_dir)

swagger_dir = os.path.join(static_dir, "swagger")
if not os.path.exists(swagger_dir):
    os.makedirs(swagger_dir)

images_path = os.path.abspath(images_dir)
swagger_path = os.path.abspath(swagger_dir)

app.mount("/static/images/", StaticFiles(directory=images_path), name="images")
app.mount("/static/swagger/", StaticFiles(directory=swagger_path), name="swagger")

app.include_router(router=ApiV2Router)
app.add_middleware(
    CORSMiddleware,
    allow_origins="*",
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version="3.0.2",
        description=app.description,
        routes=app.routes,
    )

    openapi_schema["openapi"] = "3.0.2"
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
        swagger_js_url="/static/swagger/swagger-ui-bundle.js",
        swagger_css_url="/static/swagger/swagger-ui.css",
    )

@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    return get_redoc_html(
        openapi_url=app.openapi_url,
        title=app.title + " - ReDoc",
        redoc_js_url="/static/swagger/redoc.standalone.js",
    )

@app.get("/")
def get_home():
    return {
        "message": "Welcome to Vikt"
    }

if __name__ == "__main__":
    uvicorn.run("main:app", port=8000, reload=True)