# adapters/ui/routes.py

from pathlib import Path

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from application.facades import LogiFacade
from composition.container import get_facade
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

    primary_items = (
        await facade.tracking_item_repo.list_all_by_category(primary_category.id)
        if primary_category
        else []
    )
    summary = await facade.summary()
    return templates.TemplateResponse(
        "main.html",
        {
            "request": request,
            "summary": summary,
            "has_types": len(primary_items) > 0,
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
    primary = await _get_primary_category(facade)
    secondary = await _get_secondary_category(facade)
    items = (
        await facade.tracking_item_repo.list_all_by_category(primary.id)
        if primary
        else []
    )
    content_items = (
        await facade.tracking_item_repo.list_all_by_category(secondary.id)
        if secondary
        else []
    )
    clients = await facade.client_repo.list_all()
    return templates.TemplateResponse(
        "partials/modal_log.html",
        {
            "request": request,
            "direction": direction,
            "items": items,
            "content_items": content_items,
            "clients": clients,
            "primary_category_id": primary.id if primary else "",
            "error": None,
        },
    )


@router.post("/log", response_class=HTMLResponse)
async def log_movement(
    request: Request,
    facade: LogiFacade = Depends(get_facade),
):
    form = await request.form()
    direction = str(form.get("direction") or "OUT")
    name = str(form.get("name") or "").strip()
    primary_category_id = str(form.get("primary_category_id") or "")
    notes = str(form.get("notes") or "").strip() or None

    # collect primary item quantities: fields named qty_<item_id>
    primary_item_quantities: dict[str, int] = {}
    for key, val in form.multi_items():
        if key.startswith("qty_"):
            item_id = key[4:]
            try:
                qty = int(str(val))

                if qty > 0:
                    primary_item_quantities[item_id] = qty
            except ValueError:
                pass

    # collect secondary (content) item ids: checkboxes named content_id
    secondary_item_ids: list[str] = [str(v) for v in form.getlist("content_id")]

    error = None
    try:
        if direction == "OUT":
            await facade.issue_items(
                name=name,
                primary_item_quantities=primary_item_quantities,
                secondary_item_ids=secondary_item_ids,
                notes=notes,
                primary_category_id=primary_category_id,
            )
        else:
            await facade.return_items(
                name=name,
                primary_item_quantities=primary_item_quantities,
                secondary_item_ids=secondary_item_ids,
                notes=notes,
                primary_category_id=primary_category_id,
            )
    except (UnknownContainerTypeError, InsufficientBalanceError) as e:
        error = str(e)
    except ValueError as e:
        error = str(e)
    except Exception as e:
        error = f"Unexpected error: {e}"

    if error:
        primary = await _get_primary_category(facade)
        secondary = await _get_secondary_category(facade)
        items = (
            await facade.tracking_item_repo.list_all_by_category(primary.id)
            if primary
            else []
        )
        content_items = (
            await facade.tracking_item_repo.list_all_by_category(secondary.id)
            if secondary
            else []
        )
        clients = await facade.client_repo.list_all()
        return templates.TemplateResponse(
            "partials/modal_log.html",
            {
                "request": request,
                "direction": direction,
                "items": items,
                "content_items": content_items,
                "clients": clients,
                "primary_category_id": primary_category_id,
                "error": error,
            },
        )

    summary = await facade.summary()
    return templates.TemplateResponse(
        "partials/success.html",
        {"request": request, "summary": summary},
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


@router.get("/items/content", response_class=HTMLResponse)
async def secondary_items_page(
    request: Request,
    facade: LogiFacade = Depends(get_facade),
):
    primary = await _get_primary_category(facade)
    primary_name = primary.name if primary else "Box Types"
    secondary = await _get_secondary_category(facade)

    if secondary is None:
        return templates.TemplateResponse(
            "items_secondary.html",
            {
                "request": request,
                "category": None,
                "items": [],
                "primary_category_name": primary_name,
                "category_id": None,
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
            "primary_category_name": primary_name,
            "category_id": secondary.id,
            "setup_complete": True,
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
