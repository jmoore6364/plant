"""API routes for help articles and documentation."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.connection import get_db_session
from src.database.repository import HelpArticleRepository
from src.database.models import HelpArticle

router = APIRouter(prefix="/api/help", tags=["help"])


# Pydantic schemas
class HelpArticleBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    slug: str = Field(..., min_length=1, max_length=200)
    category: str = Field(..., min_length=1, max_length=100)
    summary: str
    content: str
    tags: Optional[List[str]] = []
    icon: Optional[str] = None
    order: int = 0
    featured: bool = False
    published: bool = True
    author: Optional[str] = None
    related_article_ids: Optional[List[int]] = []


class HelpArticleResponse(HelpArticleBase):
    id: int
    view_count: int
    helpful_count: int
    not_helpful_count: int
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class HelpArticleSummary(BaseModel):
    id: int
    title: str
    slug: str
    category: str
    summary: str
    icon: Optional[str]
    featured: bool
    view_count: int

    class Config:
        from_attributes = True


# API endpoints
@router.get("/articles", response_model=List[HelpArticleSummary])
async def get_articles(
    category: Optional[str] = None,
    featured: bool = Query(False, description="Filter featured articles only"),
    db: AsyncSession = Depends(get_db_session)
):
    """Get all help articles, optionally filtered by category."""
    repo = HelpArticleRepository(db)

    if featured:
        articles = await repo.get_featured()
    else:
        articles = await repo.get_all(category=category)

    return articles


@router.get("/articles/{slug}", response_model=HelpArticleResponse)
async def get_article_by_slug(
    slug: str,
    db: AsyncSession = Depends(get_db_session)
):
    """Get a specific help article by slug."""
    repo = HelpArticleRepository(db)
    article = await repo.get_by_slug(slug)

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    # Increment view count
    await repo.increment_view_count(article.id)
    await db.commit()

    # Convert datetime objects to strings
    article_dict = {
        "id": article.id,
        "title": article.title,
        "slug": article.slug,
        "category": article.category,
        "summary": article.summary,
        "content": article.content,
        "tags": article.tags or [],
        "icon": article.icon,
        "order": article.order,
        "featured": article.featured,
        "published": article.published,
        "author": article.author,
        "related_article_ids": article.related_article_ids or [],
        "view_count": article.view_count,
        "helpful_count": article.helpful_count,
        "not_helpful_count": article.not_helpful_count,
        "created_at": article.created_at.isoformat() if article.created_at else "",
        "updated_at": article.updated_at.isoformat() if article.updated_at else "",
    }

    return article_dict


@router.get("/search", response_model=List[HelpArticleSummary])
async def search_articles(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db_session)
):
    """Search help articles by title, summary, or content."""
    repo = HelpArticleRepository(db)
    articles = await repo.search(q, limit=limit)
    return articles


@router.get("/categories", response_model=List[str])
async def get_categories(db: AsyncSession = Depends(get_db_session)):
    """Get all available help article categories."""
    repo = HelpArticleRepository(db)
    categories = await repo.get_categories()
    return categories


@router.post("/articles/{article_id}/helpful")
async def mark_article_helpful(
    article_id: int,
    helpful: bool = Query(True, description="True for helpful, False for not helpful"),
    db: AsyncSession = Depends(get_db_session)
):
    """Mark an article as helpful or not helpful."""
    repo = HelpArticleRepository(db)
    article = await repo.get_by_id(article_id)

    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    await repo.mark_helpful(article_id, helpful)
    await db.commit()

    return {"success": True, "message": "Feedback recorded"}


@router.post("/articles", response_model=HelpArticleResponse)
async def create_article(
    article: HelpArticleBase,
    db: AsyncSession = Depends(get_db_session)
):
    """Create a new help article (admin only)."""
    repo = HelpArticleRepository(db)

    # Check if slug already exists
    existing = await repo.get_by_slug(article.slug)
    if existing:
        raise HTTPException(status_code=400, detail="Article with this slug already exists")

    new_article = await repo.create(article.model_dump())
    await db.commit()

    # Convert datetime objects
    article_dict = {
        "id": new_article.id,
        "title": new_article.title,
        "slug": new_article.slug,
        "category": new_article.category,
        "summary": new_article.summary,
        "content": new_article.content,
        "tags": new_article.tags or [],
        "icon": new_article.icon,
        "order": new_article.order,
        "featured": new_article.featured,
        "published": new_article.published,
        "author": new_article.author,
        "related_article_ids": new_article.related_article_ids or [],
        "view_count": new_article.view_count,
        "helpful_count": new_article.helpful_count,
        "not_helpful_count": new_article.not_helpful_count,
        "created_at": new_article.created_at.isoformat() if new_article.created_at else "",
        "updated_at": new_article.updated_at.isoformat() if new_article.updated_at else "",
    }

    return article_dict


@router.put("/articles/{article_id}", response_model=HelpArticleResponse)
async def update_article(
    article_id: int,
    article: HelpArticleBase,
    db: AsyncSession = Depends(get_db_session)
):
    """Update an existing help article (admin only)."""
    repo = HelpArticleRepository(db)

    updated_article = await repo.update(article_id, article.model_dump())
    if not updated_article:
        raise HTTPException(status_code=404, detail="Article not found")

    await db.commit()

    # Convert datetime objects
    article_dict = {
        "id": updated_article.id,
        "title": updated_article.title,
        "slug": updated_article.slug,
        "category": updated_article.category,
        "summary": updated_article.summary,
        "content": updated_article.content,
        "tags": updated_article.tags or [],
        "icon": updated_article.icon,
        "order": updated_article.order,
        "featured": updated_article.featured,
        "published": updated_article.published,
        "author": updated_article.author,
        "related_article_ids": updated_article.related_article_ids or [],
        "view_count": updated_article.view_count,
        "helpful_count": updated_article.helpful_count,
        "not_helpful_count": updated_article.not_helpful_count,
        "created_at": updated_article.created_at.isoformat() if updated_article.created_at else "",
        "updated_at": updated_article.updated_at.isoformat() if updated_article.updated_at else "",
    }

    return article_dict


@router.delete("/articles/{article_id}")
async def delete_article(
    article_id: int,
    db: AsyncSession = Depends(get_db_session)
):
    """Delete a help article (admin only)."""
    repo = HelpArticleRepository(db)

    success = await repo.delete(article_id)
    if not success:
        raise HTTPException(status_code=404, detail="Article not found")

    await db.commit()

    return {"success": True, "message": "Article deleted"}
