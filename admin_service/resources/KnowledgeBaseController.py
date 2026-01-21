from fastapi import APIRouter, Depends, HTTPException, Request, status
from models import get_db
from models.models import ArticleCategory
from resources.utils import verify_authentication
from sqlalchemy.orm import Session

router = APIRouter()


@router.get("/category")
def list_article_category(request: Request, db: Session = Depends(get_db)):

    try:
        verify_authentication(request)

        category = (
            db.query(ArticleCategory).filter(ArticleCategory.status != "DELETED").all()
        )

        return category

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        ) from e


@router.post("/category")
def create_article_category(
    request: Request, payload: dict, db: Session = Depends(get_db)
):

    try:
        user_id, _, _ = verify_authentication(request)

        existing_category = (
            db.query(ArticleCategory)
            .filter(
                (ArticleCategory.name == payload["name"]),
                ArticleCategory.status != "DELETED",
            )
            .first()
        )

        if existing_category:
            raise HTTPException(
                status_code=409,
                detail="Article with same category name already exists",
            )

        category = ArticleCategory(
            name=payload["name"],
            status=payload.get("status"),
            order=payload.get("order"),
            created_by=user_id,
        )

        db.add(category)
        db.commit()

        return {
            "status": "Success",
            "message": "Category Saved Successfully",
            "category_id": category.id,
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        ) from e


@router.post("/updatecategory/{category_id}")
def update_article_category(
    request: Request,
    category_id: int,
    payload: dict,
    db: Session = Depends(get_db),
):
    try:
        user_id, _, _ = verify_authentication(request)

        category = (
            db.query(ArticleCategory)
            .filter(
                ArticleCategory.id == category_id, ArticleCategory.status != "DELETED"
            )
            .first()
        )
        if not category:
            raise HTTPException(404, "Article not found")

        existing_category = (
            db.query(ArticleCategory)
            .filter(
                (ArticleCategory.name == payload["name"]),
                ArticleCategory.id != category.id,
            )
            .first()
        )

        if existing_category:
            raise HTTPException(
                status_code=409,
                detail="Article with same article_name already exists",
            )

        # -----------------------------
        # UPDATE ARTICLE
        # -----------------------------
        category.name = payload.get("name", category.name)
        category.status = payload.get("status", category.status)
        category.order = payload.get("order", category.order)
        category.updated_by = user_id

        db.commit()

        return {"status": "Success", "message": "Category Updated Successfully"}

    except Exception as e:
        db.rollback()
        raise HTTPException(500, "Internal Server Error") from e


@router.post("/deletecategory/{category_id}")
def delete_article_category(
    request: Request, category_id: int, db: Session = Depends(get_db)
):

    try:
        user_id, _, _ = verify_authentication(request)
        category = (
            db.query(ArticleCategory)
            .filter(
                ArticleCategory.id == category_id, ArticleCategory.status != "DELETED"
            )
            .first()
        )
        if not category:
            raise HTTPException(404, "Article not found")

        category.status = "DELETED"
        category.updated_by = user_id

        db.commit()
        return {"status": "Success", "message": "Category Deleted Successfully"}

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        ) from e
