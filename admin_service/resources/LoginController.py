from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from models import get_db
from models.models import RolePermission, SideMenuCategory, User
from resources.utils import create_access_token, verify_hash
from sqlalchemy.orm import Session

router = APIRouter()


# -------------------------------------------------
#                       LOGIN
# -------------------------------------------------


@router.post("/login_user")
def login(request: Request, email: str, password: str, db: Session = Depends(get_db)):

    try:

        user = (
            db.query(User).filter(User.email == email, User.status != "DELETED").first()
        )

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invalid Credentials",
            )

        if not verify_hash(password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials"
            )

        access_token = create_access_token(
            data={
                "user_id": user.id,
                "user_role": user.role,
            }
        )
        request.session["loginer_details"] = access_token

        role_permissions = (
            db.query(RolePermission)
            .filter(
                RolePermission.role_id == user.role,
                RolePermission.status == "ACTIVE",
            )
            .all()
        )

        menus: dict[int, dict] = {}

        for permission in role_permissions:
            # SKIP IF ALL PERMISSIONS ARE "no"
            if not any(
                [
                    permission.add == "yes",
                    permission.edit == "yes",
                    permission.delete == "yes",
                    permission.view == "yes",
                ]
            ):
                continue

            # ------------------ Side Menu ------------------
            sidemenu = (
                db.query(SideMenuCategory)
                .filter(
                    SideMenuCategory.id == permission.menu_id,
                    SideMenuCategory.status == "ACTIVE",
                )
                .first()
            )

            if not sidemenu:
                continue

            # Create menu if not exists
            if sidemenu.id not in menus:
                menus[sidemenu.id] = {
                    "menu_id": sidemenu.id,
                    "order_no": sidemenu.order_no,
                    "menu_name": sidemenu.menu_name,
                    "menu_link": sidemenu.menu_link,
                    "menu_icon": sidemenu.menu_icon,
                    "permissions": {
                        "add": permission.add,
                        "edit": permission.edit,
                        "delete": permission.delete,
                        "view": permission.view,
                    },
                }

        # SORT MENUS BY order_no
        sorted_menus = sorted(menus.values(), key=lambda x: x["order_no"])

        menu_link = "/"

        if sorted_menus:
            first_menu = sorted_menus[0]
            menu_link = first_menu["menu_link"]

        redirect_url = menu_link

        return JSONResponse(
            content={
                "url": redirect_url,
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "role_id": user.role,
                    "token": access_token,
                },
                "rolepermission": sorted_menus,
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        ) from e
