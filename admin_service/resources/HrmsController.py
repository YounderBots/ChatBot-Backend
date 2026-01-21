from datetime import datetime

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

        db.commit()

        return {
            "status": "Success",
            "message": "Role Saved Successfully",
            "role_id": role.id,
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        ) from e


@router.post("/update_role/{role_id}")
def update_role(
    request: Request,
    role_id: int,
    payload: dict,
    db: Session = Depends(get_db),
):

    try:
        loginer_name, _, _ = verify_authentication(request)

        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise HTTPException(
                status_code=404,
                detail="Role not found",
            )

        if "name" in payload:
            existing_role = (
                db.query(Role)
                .filter(
                    Role.id != role_id,
                    Role.name == payload.get("name"),
                )
                .first()
            )

            if existing_role:
                raise HTTPException(
                    status_code=409,
                    detail="Role with same role_name already exists",
                )

        role.name = payload.get("name", role.name)
        role.updated_at = datetime.utcnow()
        role.updated_by = loginer_name

        db.query(RolePermission).filter(RolePermission.role_id == role_id).delete(
            synchronize_session=False
        )

        permissions = payload.get("permissions", [])

        for pm in permissions:
            db.add(
                RolePermission(
                    role_id=role.id,
                    menu=pm.get("menu"),
                    add=pm.get("add", False),
                    edit=pm.get("edit", False),
                    delete=pm.get("delete", False),
                    view=pm.get("view", False),
                )
            )

        db.commit()

        return {
            "status": "Success",
            "message": "Role Updated Successfully",
            "role_id": role.id,
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        ) from e
