import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi
#from starlette.middleware.cors import CORSMiddleware as CORSMiddleware
import uvicorn
from presentation import router as ApiV2Router
from config.monitoring import setup_monitoring, start_monitoring
from starlette.middleware.base import BaseHTTPMiddleware
import asyncio


app = FastAPI(
    title="Vikt API",

    description="""

                                ViktApp API помогает вам легко управлять пользователями и вопросами для проведения викторины! 🚀✨

Этот мощный API разработан для упрощения регистрации пользователей, аутентификации и управления баллами, что делает его идеальным выбором для образовательных платформ и систем викторин. 🎓📚

## Управление пользователями 👥

API предоставляет обширные функции управления пользователями, позволяя вам:

* **Регистрировать новых пользователей** – Создавайте учетные записи для пользователей, чтобы они могли получить доступ к платформе. 📝
* **Аутентифицировать пользователей** – Безопасно входите в систему с помощью их учетных данных. 🔒
* **Обновлять баллы пользователей** – Отслеживайте и изменяйте баллы пользователей на основе их результатов. 📈
* **Получать информацию о пользователях** – Получайте данные обо всех пользователях или конкретных пользователях по имени. 🔍
* **Удалять пользователей** – Удаляйте пользователей из системы при необходимости. ❌

## Управление вопросами ❓

В дополнение к управлению пользователями API предлагает надежные функции обработки вопросов:

* **Добавлять вопросы** – Заполняйте базу данных новыми вопросами из предоставленного списка. ✏️
* **Получать все вопросы** – Получайте полный список всех вопросов в базе данных. 📋
* **Фильтровать вопросы по главам** – Доступ к вопросам на основе конкретных глав для целенаправленного обучения. 📖

Это приложение построено с учетом поддерживаемости и масштабируемости, используя возможности FastAPI для предоставления быстрого и эффективного решения для бэкенда. ⚡️💻 Независимо от того, создаете ли вы приложение для викторины или образовательную платформу, ViktApp API здесь, чтобы помочь вам достичь ваших целей! 🎯🌟
    """,
    docs_url=None,  # Отключаем стандартный docs URL
    redoc_url=None,  # Отключаем стандартный redoc URL
    openapi_url="/api/openapi.json"  # Указываем свой URL для OpenAPI спецификации
)

relative_path = "static/images/"
absolute_path = os.path.abspath(relative_path)

# Создаем директории для статических файлов, если они не существуют
static_dir = "static"
if not os.path.exists(static_dir):
    os.makedirs(static_dir)

images_dir = os.path.join(static_dir, "images")
if not os.path.exists(images_dir):
    os.makedirs(images_dir)

swagger_dir = os.path.join(static_dir, "swagger")
if not os.path.exists(swagger_dir):
    os.makedirs(swagger_dir)

# Монтируем статические директории
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

class MonitoringMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # Запускаем мониторинг только один раз при первом запросе
        if not hasattr(self, '_monitoring_started'):
            setup_monitoring()
            asyncio.create_task(start_monitoring())
            self._monitoring_started = True
        
        # Продолжаем обработку запроса
        response = await call_next(request)
        return response

app.add_middleware(MonitoringMiddleware)

# Кастомная реализация OpenAPI спецификации с явным указанием версии
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version="3.0.2",  # Указываем явно версию OpenAPI
        description=app.description,
        routes=app.routes,
    )
    
    # Явно устанавливаем поле openapi в схеме
    openapi_schema["openapi"] = "3.0.2"
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Определяем пути к статическим файлам Swagger UI
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




    # gunicorn main:app  --bind 0.0.0.0:8000 --worker-class uvicorn.workers.UvicornWorker
    # fastapi run --workers 8 main.py
    # CMD ["fastapi", "run", "app/main.py", "--proxy-headers", "--port", "8000", "--host", "0.0.0.0", "--workers", "8"]
    # sudo docker system prune --all --force --volumes