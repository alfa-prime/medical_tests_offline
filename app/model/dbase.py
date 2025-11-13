import datetime
from typing import Optional

from sqlmodel import Field, SQLModel, func
from sqlalchemy import Column, DateTime, Text
from sqlalchemy.schema import UniqueConstraint
from app.core.encryption import EncryptedString


class TestResultBase(SQLModel):
    prefix: Optional[str] = None
    last_name: str
    first_name: str
    middle_name: str = Field(default="")
    birthday: datetime.date
    service_date: datetime.date
    service_name: str
    service_code: str
    result: Optional[str] = Field(default=None, sa_column=Column(Text))


class TestResult(TestResultBase, table=True):
    __tablename__ = "test_results"  # noqa

    id: Optional[int] = Field(default=None, primary_key=True, index=True)
    prefix: Optional[str]
    last_name: str
    first_name: str
    middle_name: str = Field(default="", nullable=False)
    birthday: datetime.date
    service_date: datetime.date
    service_code: str
    service_name: str
    # ВНИМАНИЕ: После миграции тип этой колонки вручную заменяется
    # на EncryptedString внутри контейнера. См. инструкцию по развертыванию.
    # Это сделано, т.к. Alembic не поддерживает автогенерацию для этого типа.
    # result: Optional[str]
    result: Optional[str] = Field(default=None, sa_column=Column(EncryptedString))
    result_hash: str | None = Field(default=None, index=True)

    created_at: Optional[datetime.datetime] = Field(
        default=None,
        sa_column=Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    )

    __table_args__ = (
        UniqueConstraint(
            'last_name',
            'first_name',
            'middle_name',
            'birthday',
            'service_date',
            'service_code',
            'result_hash',
            name='uq_patient_service_hash'
        ),
    )


class TestResultCreate(TestResultBase):
    pass


class TestResultRead(TestResultBase):
    id: int
    created_at: datetime.datetime
