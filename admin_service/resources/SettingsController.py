from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from models import get_db
from models.models import RolePermission, SideMenuCategory, User
from resources.utils import verify_authentication
from sqlalchemy.orm import Session

router = APIRouter()


# --------------------------------------------------------
#                 SETTINGS & CONFIGURATION
# --------------------------------------------------------


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
        user_id, _, _ = verify_authentication(request)

        existing_role = db.query(Role).filter((Role.name == payload["name"])).first()

        if existing_role:
            raise HTTPException(
                status_code=409,
                detail="Role with same role_name already exists",
            )

        role = Role(
            name=payload["name"],
            created_by=user_id,
        )

        db.add(role)
        db.flush()
        permissions = payload.get("permissions")

        if permissions:

            for pm in permissions:
                permission = RolePermission(
                    role_id=role.id,
                    menu_id=pm.get("menu"),
                    add=pm.get("add"),
                    edit=pm.get("edit"),
                    delete=pm.get("delete"),
                    view=pm.get("view"),
                    created_by="1",
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
