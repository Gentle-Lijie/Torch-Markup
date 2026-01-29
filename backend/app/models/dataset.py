from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    image_path = Column(String(500), nullable=False)
    label_path = Column(String(500), nullable=True)
    total_images = Column(Integer, default=0)
    labeled_images = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # 关系
    categories = relationship("Category", back_populates="dataset", cascade="all, delete-orphan")
    images = relationship("Image", back_populates="dataset", cascade="all, delete-orphan")
