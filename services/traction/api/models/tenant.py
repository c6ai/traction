from datetime import datetime
from uuid import UUID

from sqlalchemy.dialects.postgresql import UUID as SA_UUID
from sqlalchemy import UniqueConstraint, Column, DateTime, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from sqlmodel import SQLModel, Field


# shared between pydantic and SQLAlchemy models
class TenantBase(SQLModel):
    name: str
    wallet_id: UUID
    created_at: datetime = Field(default_factory=datetime.now)
    # sqlmodel.Field() doesn't have auto-update columns yet.
    updated_at: datetime = Field(
        sa_column=Column(
            DateTime(), nullable=False, default=datetime.now, onupdate=datetime.now
        )
    )


# SQLAlchemy Models, to be saved in DB
class Tenant(TenantBase, table=True):
    __table_args__ = (UniqueConstraint("name"),)

    id: UUID = Field(
        sa_column=Column(
            SA_UUID(as_uuid=True),
            server_default=text("public.gen_random_uuid()"),
            primary_key=True,
        )
    )
    is_active: bool = Field(default=True)

    @classmethod
    async def get_by_name(cls, db: AsyncSession, name: str):
        q = select(cls).where(cls.name == name)
        result = await db.execute(q)
        return result.scalars().first()


# Pydantic Models, for everything else? not sure how to hide items, would prefer
# class TenantCreate(TenantBase):
class TenantCreate(SQLModel):
    name: str