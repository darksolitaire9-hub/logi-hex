# adapters/ui/routes.py

from pathlib import Path

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse
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


# ─── Pages ────────────────────────────────────────────────────────────────────


@router.get("/", response_class=HTMLResponse)
async def main_page(request: Request, facade: LogiFacade = Depends(get_facade)):
    container_types = await facade.container_type_repo.list_all()
    summary = await facade.summary()
    return templates.TemplateResponse(
        "main.html",
        {
            "request": request,
            "container_types": container_types,
            "summary": summary,
            "has_types": len(container_types) > 0,
        },
    )


@router.get("/box-types", response_class=HTMLResponse)
async def box_types_page(request: Request, facade: LogiFacade = Depends(get_facade)):
    container_types = await facade.container_type_repo.list_all()
    return templates.TemplateResponse(
        "box_types.html",
        {
            "request": request,
            "container_types": container_types,
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
