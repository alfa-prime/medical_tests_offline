import datetime
from typing import Optional

from sqlmodel import Field, SQLModel, func
from sqlalchemy import Column, DateTime, Text, Boolean
from sqlalchemy.schema import UniqueConstraint, Index
from app.core.encryption import EncryptedString


class TestResultBase(SQLModel):
    person_id: str
    last_name: str
    first_name: str
    middle_name: str = Field(default="")
    birthday: datetime.date
    test_id: str  # внутренний id услуги в ЕВМИАС
    prefix: Optional[str] = None
    test_date: datetime.date
    service: str
    analyzer_name: Optional[str] = None
    test_code: str
    test_name: str
    is_result: bool = Field(default=False, sa_column=Column(Boolean, index=True, nullable=False))
    test_result: Optional[str] = Field(default=None, sa_column=Column(Text))


class TestResult(TestResultBase, table=True):
    __tablename__ = "test_results"  # noqa
    test_name: str = Field(sa_column=Column(EncryptedString))
    test_result: Optional[str] = Field(default=None, sa_column=Column(EncryptedString))
    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    created_at: Optional[datetime.datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    )

    __table_args__ = (
        # Уникальный индекс для отсеивания дублей
        UniqueConstraint(
            'last_name',
            'first_name',
            'middle_name',
            'birthday',
            'test_id',
            'test_date',
            'test_code',
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
