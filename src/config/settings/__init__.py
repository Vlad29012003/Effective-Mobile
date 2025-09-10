# type: ignore
from decouple import config as env_config

RUN_MODE = env_config("RUN_MODE")

if RUN_MODE == "prod":
    from .prod import *
elif RUN_MODE == "dev":
    from .dev import *
else:
    from .local import *
