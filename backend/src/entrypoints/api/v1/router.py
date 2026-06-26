from fastapi import APIRouter

from src.entrypoints.api.v1.endpoints import professors, reviews, webhooks

router = APIRouter()
router.include_router(webhooks.router)
router.include_router(reviews.router)
router.include_router(professors.router)
