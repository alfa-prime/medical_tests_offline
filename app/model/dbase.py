import datetime
from typing import Optional

from sqlmodel import Field, SQLModel, func
from sqlalchemy import Column, DateTime, Text
from sqlalchemy.schema import UniqueConstraint


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
    prefix: Optional[str] = None
    last_name: str
    first_name: str
    middle_name: str = Field(default="", nullable=False)
    birthday: datetime.date
    service_date: datetime.date
    service_code: str
    service_name: str
    result: Optional[str] = Field(default=None, sa_column=Column(Text))

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
            name='uq_patient_service'
        ),
    )


class TestResultCreate(TestResultBase):
    pass


class TestResultRead(TestResultBase):
    id: int
    created_at: datetime.datetime
