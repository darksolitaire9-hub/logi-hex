from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from application.facades import LogiFacade

from .dependencies import get_facade

router = APIRouter(prefix="/api")


class AppConfigResponse(BaseModel):
    primary_category_id: str | None
    primary_category_name: str | None
    content_category_id: str | None
    content_category_name: str | None
    is_setup_complete: bool


@router.get("/config", response_model=AppConfigResponse)
async def get_app_config(
    facade: LogiFacade = Depends(get_facade),
):
    categories = await facade.list_tracking_categories()

    primary = [c for c in categories if c.enforce_returns]
    content = [c for c in categories if not c.enforce_returns]

    if len(primary) > 1:
        raise HTTPException(
            status_code=500,
            detail="Multiple primary categories found",
        )

    primary_cat = primary[0] if primary else None
    content_cat = content[0] if content else None

    return AppConfigResponse(
        primary_category_id=primary_cat.id if primary_cat else None,
        primary_category_name=primary_cat.name if primary_cat else None,
        content_category_id=content_cat.id if content_cat else None,
        content_category_name=content_cat.name if content_cat else None,
        is_setup_complete=primary_cat is not None,
    )
