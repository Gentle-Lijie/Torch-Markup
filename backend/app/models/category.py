from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(50), nullable=False)
    shortcut_key = Column(String(10), nullable=True)
    color = Column(String(20), default="#FF0000")
    sort_order = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())

    # 关系
    dataset = relationship("Dataset", back_populates="categories")
    annotations = relationship("Annotation", back_populates="category")
