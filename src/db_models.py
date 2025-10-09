from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import declarative_base

# Baseクラスを宣言
Base = declarative_base()

# モデル定義
class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50))
    quantity = Column(Integer)
