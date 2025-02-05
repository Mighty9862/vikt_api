import asyncio
import asyncpg
import subprocess

DB_URL = "postgresql+asyncpg://admin:admin@db:5432/vikt"

async def drop_and_create_database():
    # Подключение к PostgreSQL
    conn = await asyncpg.connect(user='admin', password='admin', database='postgres', host='localhost', port='5432')
    
    # Отключаем все соединения к базе данных
    await conn.execute("SELECT pg_terminate_backend(pg_stat_activity.pid) "
                       "FROM pg_stat_activity "
                       "WHERE pg_stat_activity.datname = 'vikt' "
                       "AND pid <> pg_backend_pid();")

    # Удаляем базу данных
    await conn.execute("DROP DATABASE IF EXISTS vikt;")
    
    # Создаем новую базу данных
    await conn.execute("CREATE DATABASE vikt;")

    # Закрываем соединение с PostgreSQL
    await conn.close()

def run_alembic_commands():
    # Инициализация Alembic
    #subprocess.run(["alembic", "revision", "--autogenerate", "-m", "Initial revision"], check=True)
    subprocess.run(["alembic", "upgrade", "head"], check=True)

async def main():
    await drop_and_create_database()
    run_alembic_commands()

if __name__ == "__main__":
    asyncio.run(main())
