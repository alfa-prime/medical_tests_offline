from sqlalchemy import Column, String, DateTime, Date, Integer, Text, UniqueConstraint
from sqlalchemy.sql import func
from app.core.database import Base


class TestResult(Base):
    __tablename__ = "test_results"

    id = Column(Integer, primary_key=True, index=True)
    last_name = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    middle_name = Column(String, nullable=False, default="")
    birthday = Column(Date, nullable=False)
    service_date = Column(Date, nullable=False)
    service_name = Column(String, nullable=False)
    service_code = Column(String, nullable=False)
    service_prefix = Column(String, nullable=False)
    result = Column(Text)
    prefix = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint(
            'last_name',
            'first_name',
            'middle_name',
            'birthday',
            'service_date',
            'service_code',
            name='uq_patient_service'
        ),
    )
