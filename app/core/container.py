from dependency_injector import containers, providers

from app.core.config import configs
from app.core.database import Database
from app.repository import *
from app.services import *


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        modules=[
            "app.api.v1.endpoints.auth",
            "app.api.v1.endpoints.post",
            "app.api.v1.endpoints.tag",
            "app.api.v1.endpoints.user",
            "app.api.v1.endpoints.dataset",
            "app.api.v1.endpoints.agent",
            "app.api.v1.endpoints.visualization",
            "app.api.v2.endpoints.auth",
            "app.core.dependencies",
        ]
    )

    db = providers.Singleton(Database, db_url=configs.DATABASE_URI)

    post_repository = providers.Factory(PostRepository, session_factory=db.provided.session)
    tag_repository = providers.Factory(TagRepository, session_factory=db.provided.session)
    user_repository = providers.Factory(UserRepository, session_factory=db.provided.session)

    dataset_repository = providers.Factory(DatasetRepository, session_factory=db.provided.session)
    visualization_repository = providers.Factory(VisualizationRepository, session_factory=db.provided.session)

    auth_service = providers.Factory(AuthService, user_repository=user_repository)
    post_service = providers.Factory(PostService, post_repository=post_repository, tag_repository=tag_repository)
    tag_service = providers.Factory(TagService, tag_repository=tag_repository)
    user_service = providers.Factory(UserService, user_repository=user_repository)
    dataset_service = providers.Factory(DatasetService, repository=dataset_repository)
    agent_service = providers.Factory(AgentService, repository=dataset_repository)
    visualization_service = providers.Factory(VisualizationService, repository=visualization_repository)
