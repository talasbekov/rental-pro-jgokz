from typing import Any

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.security import get_password_hash, verify_password
from shared.models import User, UserCreate, UserUpdate

# Sentinel value: Telegram-only users cannot authenticate via password flow
TELEGRAM_AUTH_SENTINEL = "!telegram_auth_only"


async def create_user(*, session: AsyncSession, user_create: UserCreate) -> User:
    db_obj = User.model_validate(
        user_create, update={"hashed_password": get_password_hash(user_create.password)}
    )
    session.add(db_obj)
    await session.commit()
    await session.refresh(db_obj)
    return db_obj


async def update_user(
    *, session: AsyncSession, db_user: User, user_in: UserUpdate
) -> User:
    user_data = user_in.model_dump(exclude_unset=True)
    extra_data = {}
    if "password" in user_data:
        password = user_data["password"]
        hashed_password = get_password_hash(password)
        extra_data["hashed_password"] = hashed_password
    db_user.sqlmodel_update(user_data, update=extra_data)
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return db_user


async def get_user_by_email(*, session: AsyncSession, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    result = await session.exec(statement)
    return result.first()


# Dummy hash to use for timing attack prevention when user is not found
DUMMY_HASH = "$argon2id$v=19$m=65536,t=3,p=4$MjQyZWE1MzBjYjJlZTI0Yw$YTU4NGM5ZTZmYjE2NzZlZjY0ZWY3ZGRkY2U2OWFjNjk"


async def authenticate(
    *, session: AsyncSession, email: str, password: str
) -> User | None:
    db_user = await get_user_by_email(session=session, email=email)
    if not db_user:
        verify_password(password, DUMMY_HASH)
        return None
    # Telegram-only users cannot authenticate via password flow
    if db_user.hashed_password == TELEGRAM_AUTH_SENTINEL:
        return None
    verified, updated_password_hash = verify_password(password, db_user.hashed_password)
    if not verified:
        return None
    if updated_password_hash:
        db_user.hashed_password = updated_password_hash
        session.add(db_user)
        await session.commit()
        await session.refresh(db_user)
    return db_user


async def get_or_create_by_telegram_id(
    *, session: AsyncSession, telegram_id: int, full_name: str | None = None
) -> User:
    """Find existing user by telegram_id or create a new Telegram-only user."""
    result = await session.exec(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = result.first()
    if user is not None:
        return user

    user = User(
        email=f"tg_{telegram_id}@telegram.local",
        hashed_password=TELEGRAM_AUTH_SENTINEL,
        telegram_id=telegram_id,
        full_name=full_name or None,
        is_active=True,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user
