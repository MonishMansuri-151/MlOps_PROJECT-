from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from chatbot.auth.admin import require_admin
from kmeans.analytics_service import get_department_demand_analytics
from src.logger import get_logger


logger = get_logger(__name__)

router = APIRouter(
    prefix="/admin/analytics",
    tags=["Admin Analytics"]
)



templates = Jinja2Templates(
    directory="templates"
)


@router.get(
    "/dashboard",
    response_class=HTMLResponse
)
def admin_dashboard(request: Request):

    require_admin(request)

    
    return templates.TemplateResponse(
        request=request,
        name="admin_dashboard.html",
        context={}
    )

@router.get("/department-demand")
def department_demand_analytics(request: Request):

    user = require_admin(request)

    logger.info(
        f"Admin analytics requested by user_id={user['id']}"
    )

    return get_department_demand_analytics()