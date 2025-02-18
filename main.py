import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
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
    """
)

relative_path = "static/images/"
absolute_path = os.path.abspath(relative_path)

app.include_router(router=ApiV2Router)
app.mount("/static/images/", StaticFiles(directory=absolute_path), "static")
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