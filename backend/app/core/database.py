import pymysql
from pymysql.cursors import DictCursor
from contextlib import contextmanager
from .config import settings

# 解析数据库URL
def parse_database_url(url: str) -> dict:
    """解析数据库连接URL"""
    # mysql+pymysql://user:password@host:port/database
    url = url.replace("mysql+pymysql://", "")
    auth, rest = url.split("@")
    user, password = auth.split(":")
    host_port, database = rest.split("/")
    if ":" in host_port:
        host, port = host_port.split(":")
        port = int(port)
    else:
        host = host_port
        port = 3306

    return {
        "host": host,
        "port": port,
        "user": user,
        "password": password,
        "database": database,
        "charset": "utf8mb4",
        "cursorclass": DictCursor
    }

db_config = parse_database_url(settings.DATABASE_URL)


def get_connection():
    """获取数据库连接"""
    return pymysql.connect(**db_config)


@contextmanager
def get_db():
    """数据库连接上下文管理器"""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_db_dependency():
    """FastAPI 依赖注入"""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
