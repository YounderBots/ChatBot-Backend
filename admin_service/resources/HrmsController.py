from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from admin_service.models import get_db
from admin_service.models.models import Role, RolePermission
from admin_service.resources.utils import verify_authentication

router = APIRouter()


# -------------------------------------------------
# ROLE
# -------------------------------------------------


@router.get("/roles")
def list_roles(request: Request, db: Session = Depends(get_db)):

    try:
        verify_authentication(request)

        roles = db.query(Role).filter(Role.status != "DELETED").all()

        return roles

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        ) from e


@router.post("/role")
def create_role(request: Request, payload: dict, db: Session = Depends(get_db)):

    try:
        loginer_name, _, _ = verify_authentication(request)

        existing_role = db.query(Role).filter((Role.name == payload["name"])).first()

        if existing_role:
            raise HTTPException(
                status_code=409,
                detail="Role with same role_name already exists",
            )

        role = Role(
            name=payload["name"],
            created_by=loginer_name,
        )

        db.add(role)
        db.flush(role)
        permissions = payload.get("permissions")

        if permissions:

            for pm in permissions:
                permission = RolePermission(
                    role_id=role.id,
                    menu=pm.get("menu"),
                    add=pm.get("add"),
                    edit=pm.get("edit"),
                    delete=pm.get("delete"),
                    view=pm.get("view"),
                )
                db.add(permission)

        return {
            "status": "Success",
            "message": "Role Saved Successfully",
            "role_id": role.id,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        ) from e


@router.post("/update_role/{role_id}")
def update_role(
    request: Request, payload: dict, role_id: int, db: Session = Depends(get_db)
):

    try:
        loginer_name, _, _ = verify_authentication(request)

        role = db.query(Role).filter(Role.id == role_id, Role.status == "ACTIVE")

        existing_role = db.query(Role).filter((Role.name == payload["name"])).first()

        if existing_role:
            raise HTTPException(
                status_code=409,
                detail="Role with same role_name already exists",
            )

        role = Role(
            name=payload["name"],
            created_by=loginer_name,
        )

        db.add(role)
        db.flush(role)
        permissions = payload.get("permissions")

        if permissions:

            for pm in permissions:
                permission = RolePermission(
                    role_id=role.id,
                    menu=pm.get("menu"),
                    add=pm.get("add"),
                    edit=pm.get("edit"),
                    delete=pm.get("delete"),
                    view=pm.get("view"),
                )
                db.add(permission)

        return {
            "status": "Success",
            "message": "Role Saved Successfully",
            "role_id": role.id,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        ) from e
