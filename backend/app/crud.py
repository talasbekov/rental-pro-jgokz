import uuid

from sqlmodel.ext.asyncio.session import AsyncSession

from shared.crud.users import (  # noqa: F401
    DUMMY_HASH,
    TELEGRAM_AUTH_SENTINEL,
    authenticate,
    create_user,
    get_or_create_by_telegram_id,
    get_user_by_email,
    update_user,
)
from shared.models import Item, ItemCreate


async def create_item(
    *, session: AsyncSession, item_in: ItemCreate, owner_id: uuid.UUID
) -> Item:
    db_item = Item.model_validate(item_in, update={"owner_id": owner_id})
    session.add(db_item)
    await session.commit()
    await session.refresh(db_item)
    return db_item
