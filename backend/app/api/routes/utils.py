from fastapi import APIRouter, Depends
from pydantic.networks import EmailStr

from app.api.deps import RedisDep, get_current_active_superuser
from app.models import Message
from app.utils import generate_test_email, send_email

router = APIRouter(prefix="/utils", tags=["utils"])


@router.post(
    "/test-email/",
    dependencies=[Depends(get_current_active_superuser)],
    status_code=201,
)
async def test_email(email_to: EmailStr) -> Message:
    """
    Test emails.
    """
    email_data = generate_test_email(email_to=email_to)
    send_email(
        email_to=email_to,
        subject=email_data.subject,
        html_content=email_data.html_content,
    )
    return Message(message="Test email sent")


@router.get("/health-check/")
async def health_check() -> bool:
    return True


@router.get("/redis-health/")
async def redis_health(redis_client: RedisDep) -> dict[str, str]:
    result = await redis_client.ping()
    return {"status": "ok" if result else "error"}
