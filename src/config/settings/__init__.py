# type: ignore
from decouple import config as env_config

RUN_MODE = env_config("RUN_MODE")

if RUN_MODE == "prod":
    from .prod import *  # noqa: F403
elif RUN_MODE == "dev":
    from .dev import *  # noqa: F403
else:
    from .local import *  # noqa: F403
