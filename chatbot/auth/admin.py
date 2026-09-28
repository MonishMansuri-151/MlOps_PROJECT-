from fastapi import HTTPException, Request


ADMIN_ROLES = {"admin", "super_admin"}


def get_current_admin(request: Request):
    return request.session.get("admin_user")


def require_admin(request: Request):
    admin = get_current_admin(request)

    if not admin:
        raise HTTPException(
            status_code=401,
            detail="Please login as admin."
        )

    role = str(admin.get("role", "")).lower()

    if role not in ADMIN_ROLES:
        raise HTTPException(
            status_code=403,
            detail="Admin access required."
        )

    return admin