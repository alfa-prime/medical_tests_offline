import datetime
from typing import Optional

from sqlmodel import Field, SQLModel, func
from sqlalchemy import Column, DateTime, Text
from sqlalchemy.schema import UniqueConstraint, Index
from app.core.encryption import EncryptedString


class TestResultBase(SQLModel):
    prefix: Optional[str] = None
    last_name: str
    first_name: str
    middle_name: str = Field(default="")
    birthday: datetime.date
    service: str
    analyzer_name: str
    test_date: datetime.date
    test_code: str
    test_name: str
    test_result: Optional[str] = Field(default=None, sa_column=Column(Text))


class TestResult(TestResultBase, table=True):
    __tablename__ = "test_results"  # noqa
    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    result_hash: str | None = Field(default=None, index=True)
    created_at: Optional[datetime.datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    )
    test_result: Optional[str] = Field(default=None, sa_column=Column(EncryptedString))

    __table_args__ = (
        # Уникальный индекс для отсеивания дублей
        UniqueConstraint(
            'last_name',
            'first_name',
            'middle_name',
            'birthday',
            'test_date',
            'test_code',
            'result_hash',
            name='uq_patient_service_hash'
        ),
        # Композитный индекс для ускорения поиска
        Index(
            'ix_test_results_patient_search',
            'last_name',
            'first_name',
            'middle_name',
            'birthday'
        ),
    )


class TestResultCreate(TestResultBase):
    pass


class TestResultRead(TestResultBase):
    id: int
    created_at: datetime.datetime
