from sqlalchemy import Column, Integer, Date, ForeignKey
from app.core.database import Base


class WorkStatistics(Base):
    __tablename__ = "work_statistics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    dataset_id = Column(Integer, ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    images_labeled = Column(Integer, default=0)
    annotations_created = Column(Integer, default=0)
    time_spent = Column(Integer, default=0)
