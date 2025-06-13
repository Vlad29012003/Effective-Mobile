import os

from decouple import AutoConfig, Config, RepositoryEmpty


class RepositorySecret(RepositoryEmpty):
    def __init__(self, source):  # noqa
        self.data = {}

        if not os.path.isdir(source):
            return

        ls = os.listdir(source)

        for file in ls:
            if os.path.isdir(os.path.join(source, file)):
                continue

            with open(os.path.join(source, file)) as f:
                self.data[file.upper()] = f.read()

    def __contains__(self, key):
        return key in os.environ or key in self.data

    def __getitem__(self, key):
        return self.data[key]


class CompositeRepository:
    def __init__(self, *repositories):
        self.repositories = repositories

    def __contains__(self, key):
        return any(key in repo for repo in self.repositories)

    def __getitem__(self, key):
        for repo in self.repositories:
            if key in repo:
                return repo[key]
        raise KeyError(key)


autoconfig = AutoConfig()
SECRETS_PATH = autoconfig("SECRETS_PATH", default="/run/secrets/")

repository = CompositeRepository(autoconfig.config.repository, RepositorySecret(SECRETS_PATH))

config = Config(repository)
