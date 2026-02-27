# adapters/ui/routes.py

from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from application.facades import LogiFacade
from composition.container import get_facade
from domain.entities import ContainerType
from domain.exceptions import InsufficientBalanceError, UnknownContainerTypeError

BASE_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

router = APIRouter(prefix="/ui", tags=["ui"])


def _slug(name: str) -> str:
    """Auto-generate an ID from a label. 'White Box' -> 'white-box'"""
    return name.lower().strip().replace(" ", "-")


async def _is_setup_complete(facade: LogiFacade) -> bool:
    """True if at least one balanced (primary) category exists."""
    categories = await facade.tracking_category_repo.list_all()
    return any(c.is_balanced for c in categories)


# ─── Pages ────────────────────────────────────────────────────────────────────


@router.get("/", response_class=HTMLResponse)
async def main_dashboard(
    request: Request,
    facade: LogiFacade = Depends(get_facade),
):
    categories = await facade.tracking_category_repo.list_all()
    if not categories:
        return RedirectResponse(url="/ui/setup", status_code=status.HTTP_302_FOUND)

    primary_category = next(
        (c for c in categories if c.is_balanced),
        None,
    )
    primary_name = primary_category.name if primary_category else "Box Types"

    container_types = await facade.container_type_repo.list_all()
    summary = await facade.summary()
    return templates.TemplateResponse(
        "main.html",
        {
            "request": request,
            "container_types": container_types,
            "summary": summary,
            "has_types": len(container_types) > 0,
            "primary_category_name": primary_name,
            "setup_complete": True,
        },
    )


@router.get("/box-types", response_class=HTMLResponse)
async def box_types_page(request: Request, facade: LogiFacade = Depends(get_facade)):
    categories = await facade.tracking_category_repo.list_all()
    primary_category = next(
        (c for c in categories if c.is_balanced),
        None,
    )
    primary_name = primary_category.name if primary_category else "Box Types"

    container_types = await facade.container_type_repo.list_all()
    return templates.TemplateResponse(
        "box_types.html",
        {
            "request": request,
            "container_types": container_types,
            "primary_category_name": primary_name,
            "setup_complete": True,
        },
    )


# ─── HTMX partials ────────────────────────────────────────────────────────────


@router.get("/modal/log", response_class=HTMLResponse)
async def modal_log(
    request: Request,
    direction: str,  # "OUT" or "IN"
    facade: LogiFacade = Depends(get_facade),
):
    container_types = await facade.container_type_repo.list_all()
    clients = await facade.client_repo.list_all()
    return templates.TemplateResponse(
        "partials/modal_log.html",
        {
            "request": request,
            "direction": direction,
            "container_types": container_types,
            "clients": clients,
            "error": None,
        },
    )


@router.post("/log", response_class=HTMLResponse)
async def log_movement(
    request: Request,
    facade: LogiFacade = Depends(get_facade),
    direction: str = Form(...),
    name: str = Form(...),
    container_type_id: str = Form(...),
    quantity: int = Form(...),
):
    error = None
    try:
        if direction == "OUT":
            await facade.issue(
                name=name,
                container_type_id=container_type_id,
                quantity=quantity,
            )
        else:
            await facade.receive(
                name=name,
                container_type_id=container_type_id,
                quantity=quantity,
            )
    except (UnknownContainerTypeError, InsufficientBalanceError) as e:
        error = str(e)
    except Exception as e:
        error = f"Unexpected error: {e}"

    if error:
        # re-render modal with error, don't close
        container_types = await facade.container_type_repo.list_all()
        clients = await facade.client_repo.list_all()
        return templates.TemplateResponse(
            "partials/modal_log.html",
            {
                "request": request,
                "direction": direction,
                "container_types": container_types,
                "clients": clients,
                "error": error,
            },
        )

    # success: close modal + refresh summary
    summary = await facade.summary()
    return templates.TemplateResponse(
        "partials/success.html",
        {
            "request": request,
            "summary": summary,
        },
    )


@router.get("/partial/summary", response_class=HTMLResponse)
async def summary_partial(request: Request, facade: LogiFacade = Depends(get_facade)):
    summary = await facade.summary()
    return templates.TemplateResponse(
        "partials/summary.html",
        {
            "request": request,
            "summary": summary,
        },
    )


@router.post("/box-types/add", response_class=HTMLResponse)
async def add_box_type(
    request: Request,
    facade: LogiFacade = Depends(get_facade),
    label: str = Form(...),
):
    ct = ContainerType(id=_slug(label), label=label.strip())
    await facade.container_type_repo.save(ct)
    await facade.uow.commit()
    container_types = await facade.container_type_repo.list_all()
    return templates.TemplateResponse(
        "partials/box_types_table.html",
        {
            "request": request,
            "container_types": container_types,
        },
    )


@router.post("/box-types/delete", response_class=HTMLResponse)
async def delete_box_type(
    request: Request,
    facade: LogiFacade = Depends(get_facade),
    type_id: str = Form(...),
):
    await facade.container_type_repo.delete(type_id)
    await facade.uow.commit()
    container_types = await facade.container_type_repo.list_all()
    return templates.TemplateResponse(
        "partials/box_types_table.html",
        {
            "request": request,
            "container_types": container_types,
        },
    )


# ─── Tracking items management ────────────────────────────────────────────────


async def _get_primary_category(facade: LogiFacade):
    categories = await facade.tracking_category_repo.list_all()
    return next((c for c in categories if c.is_balanced), None)


async def _get_secondary_category(facade: LogiFacade):
    categories = await facade.tracking_category_repo.list_all()
    return next((c for c in categories if not c.is_balanced), None)


@router.get("/items/primary", response_class=HTMLResponse)
async def primary_items_page(
    request: Request,
    facade: LogiFacade = Depends(get_facade),
):
    primary = await _get_primary_category(facade)
    if primary is None:
        # Force setup if somehow no primary exists
        return RedirectResponse(url="/ui/setup", status_code=status.HTTP_302_FOUND)

    items = await facade.tracking_item_repo.list_all_by_category(primary.id)

    return templates.TemplateResponse(
        "items_primary.html",
        {
            "request": request,
            "category": primary,
            "items": items,
            "primary_category_name": primary.name,
            "category_id": primary.id,
            "setup_complete": True,
        },
    )


@router.get("items_secondary.html", response_class=HTMLResponse)
async def secondary_items_page(
    request: Request,
    facade: LogiFacade = Depends(get_facade),
):
    secondary = await _get_secondary_category(facade)
    if secondary is None:
        # No secondary category yet; show a simple message
        return templates.TemplateResponse(
            "items_secondary.html",
            {
                "request": request,
                "category": None,
                "items": [],
                "primary_category_name": "Box Types",
                "category_id": secondary.id if secondary else None,
                "setup_complete": True,
            },
        )

    items = await facade.tracking_item_repo.list_all_by_category(secondary.id)

    return templates.TemplateResponse(
        "items_secondary.html",
        {
            "request": request,
            "category": secondary,
            "items": items,
            "primary_category_name": "Box Types",
        },
    )


@router.get("/setup", response_class=HTMLResponse)
async def setup_home(
    request: Request,
    facade: LogiFacade = Depends(get_facade),
):
    return templates.TemplateResponse(
        "setup.html",
        {
            "request": request,
            "primary_category_name": "Box Types",
            "setup_complete": False,
        },
    )
