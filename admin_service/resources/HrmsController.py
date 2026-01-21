import shutil
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from admin_service.models import get_db
from admin_service.models.models import Role, RolePermission, User
from admin_service.resources.utils import hash_text, verify_authentication

router = APIRouter()


# -------------------------------------------------
#                       ROLE
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
        db.flush(role)
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
        user_id, _, _ = verify_authentication(request)

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

        role.status = "INACTIVE"
        role.updated_by = user_id

        permissions = (
            db.query(RolePermission).filter(RolePermission.role_id == role_id).all()
        )

        for permission in permissions:
            permission.status = "INACTIVE"

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


@router.post("/users")
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

        image = payload.get("profile_image")
        if image:
            upload_file = image.content_type
            extention = upload_file.split("/")[-1]
            token_photo = str(uuid.uuid4()) + "." + str(extention)
            file_location = f"./templates/static/uploaded_imge/{token_photo}"
            with open(file_location, "wb+") as file_object:
                shutil.copyfileobj(image.file, file_object)

        user = User(
            fullname=payload.get("fullname"),
            email=payload.get("email"),
            password=hashed_password,
            role=payload.get("role"),
            email_notification=payload.get("email_notification"),
            profile_image=file_location,
            created_by=user_id,
        )
        db.add(user)
        db.commit()

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        ) from e


@router.get("/users")
def fetch_users(request: Request, db: Session = Depends(get_db)):
    try:
        verify_authentication(request)

        users = db.query(User).filter(User.status != "DELETED").all()

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


@router.post("/update_user/{user_id}")
def update_user(
    request: Request, user_id: int, payload: dict, db: Session = Depends(get_db)
):
    try:
        user_id, _, _ = verify_authentication(request)

        existing_user = (
            db.query(User)
            .filter(
                User.email == payload["email"],
                User.id != user_id,
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
            db.query(User).filter(User.id == user_id, User.status != "DELETED").first()
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User Not Found",
            )

        password = payload.get("password")
        if password:
            password = hash_text(password)

        image = payload.get("profile_image")
        if image:
            upload_file = image.content_type
            extention = upload_file.split("/")[-1]
            token_photo = str(uuid.uuid4()) + "." + str(extention)
            file_location = f"./templates/static/uploaded_imge/{token_photo}"
            with open(file_location, "wb+") as file_object:
                shutil.copyfileobj(image.file, file_object)

        user.full_name = payload.get("fullname", user.full_name)
        user.email = payload.get("email", user.email)
        user.password = password if password else user.password
        user.profile_image = file_location if image else user.profile_image
        user.email_notification = payload.get(
            "email_notification", user.email_notification
        )
        user.role = payload.get("role", user.role)
        user.status = payload.get("status", user.status)
        user.updated_by = user_id

        db.commit()

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        ) from e


@router.post("/delete_user/{user_id}")
def delete_user(request: Request, user_id: int, db: Session = Depends(get_db)):
    try:
        user_id, _, _ = verify_authentication(request)

        user = (
            db.query(User).filter(User.id == user_id, User.status != "DELETED").first()
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User Not Found",
            )

        user.status = "DELETED"
        user.updated_by = user_id

        db.commit()

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        ) from e
