from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.post import router as post_router
from app.api.v1.endpoints.tag import router as tag_router
from app.api.v1.endpoints.user import router as user_router
from app.api.v1.endpoints.dataset import router as dataset_router
from app.api.v1.endpoints.agent import router as agent_router

routers = APIRouter()
router_list = [auth_router, post_router, tag_router, user_router, dataset_router, agent_router]

for router in router_list:
    router.tags = routers.tags.append("v1")
    routers.include_router(router)
