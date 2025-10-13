import os
import urllib.parse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv

# # .env をロード
# load_dotenv()

# SQLiteファイルの保存先
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "app.db")


def get_connection_uri() -> str:
    """SQLiteの接続URIを生成"""
    return f"sqlite:///{DB_PATH}"
    # """PostgreSQLの接続URIを生成"""
    # db_host = os.getenv("PGHOST")
    # db_name = os.getenv("PGDATABASE")
    # db_user = os.getenv("PGUSER")
    # db_password = urllib.parse.quote_plus(os.getenv("PGPASSWORD", ""))
    # ssl_mode = os.getenv("PGSSLMODE", "require")

    # return f"postgresql://{db_user}:{db_password}@{db_host}/{db_name}?sslmode={ssl_mode}"


# SQLAlchemyエンジンとセッション
DATABASE_URL = get_connection_uri()
engine = create_engine(DATABASE_URL, echo=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Session:
    """FastAPI依存注入用のDBセッション"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
