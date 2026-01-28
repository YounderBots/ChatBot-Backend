import base64
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from models import get_db
from models.models import Article, ArticleCategory, RelatedQuestion, User
from resources.utils import handle_featured_image, verify_authentication
from sqlalchemy.orm import Session

router = APIRouter()


@router.get("/category")
def list_article_category(request: Request, db: Session = Depends(get_db)):

    try:
        verify_authentication(request)

        categories = (
            db.query(ArticleCategory).filter(ArticleCategory.status != "DELETED").all()
        )

        result = []

        for category in categories:
            count = (
                db.query(Article)
                .filter(Article.category == category.id, Article.status != "DELETED")
                .count()
            )
            result.append(
                {
                    "id": category.id,
                    "name": category.name,
                    "count": count if count else 0,
                    "order": category.order,
                    "last_modified": (
                        category.updated_at
                        if category.updated_at
                        else category.created_at
                    ),
                }
            )

        return result

    except Exception as e:
        print(e)
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


@router.get("/article")
def list_articles(request: Request, db: Session = Depends(get_db)):
    try:
        verify_authentication(request)

        articles = (
            db.query(Article)
            .filter(Article.status != "DELETED")
            .order_by(Article.created_at.desc())
            .all()
        )

        result = []

        for a in articles:
            questions = []
            question = (
                db.query(RelatedQuestion)
                .filter(
                    RelatedQuestion.article_id == a.id,
                    RelatedQuestion.status != "DELETED",
                )
                .all()
            )
            category = (
                db.query(ArticleCategory)
                .filter(
                    ArticleCategory.id == a.category,
                    ArticleCategory.status != "DELETED",
                )
                .first()
            )
            author = db.query(User).filter(User.id == int(a.created_by)).first()
            for q in question:
                questions.append({"id": q.id, "question": q.question})

            result.append(
                {
                    "id": a.id,
                    "title": a.title,
                    "category_id": a.category,
                    "category": category.name,
                    "article_status": a.article_status,
                    "url": a.url,
                    "tags": [t.strip() for t in a.tags.split(",")] if a.tags else [],
                    "contents": a.contents,
                    "meta_description": a.meta_description,
                    "featured_image": a.featured_image,
                    "featured_article": int(a.featured_article),
                    "publish_date": a.publish_date,
                    "questions": questions,
                    "published": a.created_by,
                    "updated_at": a.updated_at if a.updated_at else a.created_at,
                    "author": author.fullname if a.created_by else "-",
                }
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        ) from e


@router.post("/article")
def create_article(request: Request, payload: dict, db: Session = Depends(get_db)):

    try:
        user_id, _, _ = verify_authentication(request)
        print(payload)

        existing_article = (
            db.query(Article)
            .filter(
                (Article.title == payload["title"]),
                Article.status != "DELETED",
            )
            .first()
        )

        if existing_article:
            raise HTTPException(
                status_code=409,
                detail="Article with same title already exists",
            )

        tags = payload.get("tags")

        file_location = handle_featured_image(payload.get("featured_image"))

        article = Article(
            title=payload["title"],
            url=payload["url"],
            category=payload["category_id"],
            tags=",".join(tags),
            contents=payload.get("contents"),
            meta_description=payload.get("meta_description"),
            featured_image=file_location,
            featured_article=payload.get("featured_article"),
            publish_date=payload.get("publish_date"),
            article_status=payload.get("article_status"),
            created_by=user_id,
        )

        db.add(article)
        db.commit()
        db.refresh(article)

        related_questions = payload.get("related_questions")

        if related_questions:
            for question in related_questions:
                rq = RelatedQuestion(
                    article_id=article.id,
                    question=question.get("question"),
                    created_by=user_id,
                )
                db.add(rq)
                db.commit()
                db.refresh(rq)
        db.commit()

        return {
            "status": "Success",
            "message": "Article Saved Successfully",
            "article_id": article.id,
        }

    except Exception as e:
        db.rollback()
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        ) from e


@router.get("/article/{article_id}")
def view_article(
    request: Request,
    article_id: int,
    db: Session = Depends(get_db),
):
    try:
        verify_authentication(request)

        article = (
            db.query(Article)
            .filter(
                Article.id == article_id,
                Article.status != "DELETED",
            )
            .first()
        )

        if not article:
            raise HTTPException(status_code=404, detail="Article not found")

        related_questions = (
            db.query(RelatedQuestion)
            .filter(
                RelatedQuestion.article_id == article.id,
                RelatedQuestion.status != "DELETED",
            )
            .all()
        )

        return {
            "id": article.id,
            "title": article.title,
            "url": article.url,
            "category_id": article.category,
            "tags": article.tags,
            "contents": article.contents,
            "meta_description": article.meta_description,
            "featured_image": article.featured_image,
            "featured_article": article.featured_article,
            "publish_date": article.publish_date,
            "article_status": article.article_status,
            "created_at": article.created_at,
            "updated_at": article.updated_at,
            "related_questions": [q.question for q in related_questions],
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        ) from e


@router.post("/article/{article_id}")
def update_article(
    request: Request,
    article_id: int,
    payload: dict,
    db: Session = Depends(get_db),
):
    try:
        user_id, _, _ = verify_authentication(request)

        article = (
            db.query(Article)
            .filter(
                Article.id == article_id,
                Article.status != "DELETED",
            )
            .first()
        )

        if not article:
            raise HTTPException(status_code=404, detail="Article not found")

        # Check duplicate title
        existing_article = (
            db.query(Article)
            .filter(
                Article.title == payload["title"],
                Article.id != article.id,
                Article.status != "DELETED",
            )
            .first()
        )

        if existing_article:
            raise HTTPException(
                status_code=409,
                detail="Article with same title already exists",
            )

        file_location = handle_featured_image(payload.get("featured_image"))

        # -----------------------------
        # UPDATE ARTICLE FIELDS
        # -----------------------------
        article.title = payload.get("title", article.title)
        article.url = payload.get("url", article.url)
        article.category = payload.get("category_id", article.category)
        article.tags = payload["tags"] = (
            ",".join(payload["tags"]) if payload.get("tags") else article.tags
        )
        article.contents = payload.get("contents", article.contents)
        article.meta_description = payload.get(
            "meta_description", article.meta_description
        )
        article.featured_image = (
            file_location if payload.get("featured_image") else article.featured_image
        )
        article.featured_article = payload.get(
            "featured_article", article.featured_article
        )
        article.publish_date = payload.get("publish_date", article.publish_date)
        article.article_status = payload.get("article_status", article.article_status)
        article.updated_by = user_id

        # -----------------------------
        # UPDATE RELATED QUESTIONS
        # -----------------------------
        related_questions = payload.get("related_questions")
        print(payload)
        print(related_questions)

        if related_questions is not None:
            print("processing related questions")

            # delete old ones
            db.query(RelatedQuestion).filter(
                RelatedQuestion.article_id == article.id,
                RelatedQuestion.status != "DELETED",
            ).delete(synchronize_session=False)

            # insert new ones
            for q in related_questions:
                question_text = q.get("question") if isinstance(q, dict) else q

                if question_text:  # avoid empty inserts
                    rq = RelatedQuestion(
                        article_id=article.id,
                        question=question_text,
                        created_by=user_id,
                    )
                    db.add(rq)

        db.commit()

        return {
            "status": "Success",
            "message": "Article Updated Successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        print(e)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        ) from e


@router.post("/article/delete/{article_id}")
def delete_article(
    request: Request,
    article_id: int,
    db: Session = Depends(get_db),
):
    try:
        user_id, _, _ = verify_authentication(request)

        article = (
            db.query(Article)
            .filter(
                Article.id == article_id,
                Article.status != "DELETED",
            )
            .first()
        )

        if not article:
            raise HTTPException(status_code=404, detail="Article not found")

        article.status = "DELETED"
        article.updated_by = user_id

        related_questions = (
            db.query(RelatedQuestion)
            .filter(
                RelatedQuestion.article_id == article.id,
                RelatedQuestion.status != "DELETED",
            )
            .all()
        )
        for question in related_questions:
            question.status = "DELETED"
            question.updated_by = user_id

        db.commit()

        return {
            "status": "Success",
            "message": "Article Deleted Successfully",
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error",
        ) from e
