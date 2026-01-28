from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from models import get_db
from models.models import Role, RolePermission, SideMenuCategory, User
from resources.utils import handle_featured_image, hash_text, verify_authentication
from sqlalchemy.orm import Session

router = APIRouter()


# -------------------------------------------------
#                       MENU
# -------------------------------------------------


@router.get("/menus")
def list_menus(request: Request, db: Session = Depends(get_db)):

    try:
        verify_authentication(request)

        menus = (
            db.query(SideMenuCategory)
            .filter(SideMenuCategory.status != "DELETED")
            .order_by(SideMenuCategory.order_no.asc())
            .all()
        )

        result = []

        for menu in menus:
            result.append({"id": menu.id, "menu": menu.menu_name})

        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        ) from e


# -------------------------------------------------
#                       ROLE
# -------------------------------------------------


@router.get("/roles")
def list_roles(request: Request, db: Session = Depends(get_db)):

    try:
        verify_authentication(request)

        roles = db.query(Role).filter(Role.status != "DELETED").all()

        for role in roles:
            permission = (
                db.query(RolePermission)
                .filter(
                    RolePermission.role_id == role.id,
                    RolePermission.status != "DELETED",
                )
                .all()
            )

            role.permission = permission

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

        existing_role = (
            db.query(Role)
            .filter((Role.name == payload["name"]), Role.status != "DELETED")
            .first()
        )

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
                    created_by=user_id,
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
        print(e)
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
        user_id, _, _ = verify_authentication(request)

        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise HTTPException(
                status_code=404,
                detail="Role not found",
            )

        existing_role = (
            db.query(Role)
            .filter(
                Role.id != role_id,
                Role.name == payload.get("name"),
                Role.status != "DELETED",
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
        role.updated_by = user_id

        db.query(RolePermission).filter(RolePermission.role_id == role_id).delete(
            synchronize_session=False
        )

        permissions = payload.get("permissions", [])

        for pm in permissions:
            db.add(
                RolePermission(
                    role_id=role.id,
                    menu_id=pm.get("menu"),
                    add=pm.get("add", False),
                    edit=pm.get("edit", False),
                    delete=pm.get("delete", False),
                    view=pm.get("view", False),
                    created_by=user_id,
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
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        ) from e


@router.post("/delete_role/{role_id}")
def delete_role(
    request: Request,
    role_id: int,
    db: Session = Depends(get_db),
):

    try:
        user_id, _, _ = verify_authentication(request)

        role = db.query(Role).filter(Role.id == role_id).first()
        if not role:
            raise HTTPException(
                status_code=404,
                detail="Role not found",
            )

        role.status = "DELETED"
        role.updated_by = user_id

        permissions = (
            db.query(RolePermission).filter(RolePermission.role_id == role_id).all()
        )

        for permission in permissions:
            permission.status = "DELETED"

        db.commit()

        return {
            "status": "Success",
            "message": "Role Deleted Successfully",
            "role_id": role.id,
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        ) from e


# -------------------------------------------------
#                       USER
# -------------------------------------------------


@router.post("/user")
def create_users(request: Request, payload: dict, db: Session = Depends(get_db)):
    try:
        user_id, _, _ = verify_authentication(request)

        existing_user = (
            db.query(User)
            .filter(User.email == payload["email"], User.status != "DELETED")
            .first()
        )
        if existing_user:
            raise HTTPException(
                status_code=409,
                detail="User with same email already exists",
            )

        password = payload.get("password")
        hashed_password = hash_text(password)

        file_location = handle_featured_image(payload.get("profile_image"))

        user = User(
            fullname=payload.get("fullname"),
            email=payload.get("email"),
            password=hashed_password,
            role=int(payload.get("role")),
            email_notification=payload.get("email_notification"),
            profile_image=file_location,
            created_by=user_id,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        return {
            "status": "Success",
            "message": "User Added Successfully",
            "user_id": user.id,
        }

    except Exception as e:
        db.rollback()
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        ) from e


@router.get("/users")
def fetch_users(request: Request, db: Session = Depends(get_db)):
    try:
        verify_authentication(request)

        users = db.query(User).filter(User.status != "DELETED").all()

        for user in users:

            roles = (
                db.query(Role)
                .filter(Role.id == user.role, Role.status != "DELETED")
                .first()
            )
            if roles:
                user.roleName = roles.name
                user.role = roles.id

        return users

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        ) from e


@router.get("/user/{user_id}")
def fetch_user(request: Request, user_id: int, db: Session = Depends(get_db)):
    try:
        verify_authentication(request)

        user = (
            db.query(User).filter(User.id == user_id, User.status != "DELETED").first()
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User Not Found",
            )

        return user

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        ) from e


@router.post("/update_user/{update_user_id}")
def update_user(
    request: Request, update_user_id: int, payload: dict, db: Session = Depends(get_db)
):
    try:
        user_id, _, _ = verify_authentication(request)
        print(payload)

        existing_user = (
            db.query(User)
            .filter(
                User.email == payload["email"],
                User.id != update_user_id,
                User.status != "DELETED",
            )
            .first()
        )
        if existing_user:
            raise HTTPException(
                status_code=409,
                detail="User with same email already exists",
            )

        user = (
            db.query(User)
            .filter(User.id == update_user_id, User.status != "DELETED")
            .first()
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User Not Found",
            )

        password = payload.get("password")
        if password:
            password = hash_text(password)

        file_location = handle_featured_image(payload.get("profile_image"))

        user.fullname = payload.get("fullname", user.fullname)
        user.email = payload.get("email", user.email)
        user.password = password if password else user.password
        user.profile_image = (
            file_location if payload.get("profile_image") else user.profile_image
        )
        user.email_notification = payload.get(
            "email_notification", user.email_notification
        )
        user.role = payload.get("role", user.role)
        user.status = "ACTIVE" if payload.get("status", user.status) else "INACTIVE"
        user.updated_by = user_id

        db.commit()

        return {
            "status": "Success",
            "message": "User Updated Successfully",
            "user_id": user.id,
        }

    except Exception as e:
        db.rollback()
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        ) from e


@router.post("/update_user_status/{update_user_id}")
def update_user_status(
    request: Request, update_user_id: int, payload: dict, db: Session = Depends(get_db)
):
    try:
        user_id, _, _ = verify_authentication(request)

        user = (
            db.query(User)
            .filter(User.id == update_user_id, User.status != "DELETED")
            .first()
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User Not Found",
            )

        user.status = payload.get("status", user.status)
        user.updated_by = user_id

        db.commit()

        return {
            "status": "Success",
            "message": "User Status Updated Successfully",
            "user_id": user.id,
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        ) from e


@router.post("/delete_user/{delete_user_id}")
def delete_user(request: Request, delete_user_id: int, db: Session = Depends(get_db)):
    try:
        user_id, _, _ = verify_authentication(request)

        user = (
            db.query(User)
            .filter(User.id == delete_user_id, User.status != "DELETED")
            .first()
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User Not Found",
            )

        user.status = "DELETED"
        user.updated_by = user_id

        db.commit()

        return {
            "status": "Success",
            "message": "User Deleted Successfully",
            "user_id": user.id,
        }

    except Exception as e:
        db.rollback()
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        ) from e


@router.get("/agents/available")
def get_available_agents(db: Session = Depends(get_db)):
    """
    Returns available support agents
    """

    agents = (
        db.query(User)
        .join(Role, Role.id == User.role)
        .filter(Role.name == "AGENT", User.status == "ACTIVE")
        .all()
    )

    return {
        "agents": [
            {"id": agent.id, "name": agent.fullname, "email": agent.email}
            for agent in agents
        ]
    }
