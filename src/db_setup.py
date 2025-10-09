from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from get_conn import get_connection_uri
from db_models import Base, Inventory

# 接続文字列を取得
conn_string = get_connection_uri()

# エンジンとセッション作成
engine = create_engine(conn_string)
SessionLocal = sessionmaker(bind=engine)
session = SessionLocal()

# テーブル作成（存在する場合は削除して再作成）
Base.metadata.drop_all(bind=engine)  # ← DROP TABLE
Base.metadata.create_all(bind=engine)  # ← CREATE TABLE
print("Finished creating table")

# データ挿入
items = [
    Inventory(name="banana", quantity=150),
    Inventory(name="orange", quantity=154),
    Inventory(name="apple", quantity=100),
]
session.add_all(items)
session.commit()
print("Inserted 3 rows of data")

# クリーンアップ
session.close()
engine.dispose()
print("Connection closed")
