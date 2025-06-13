class RequiredActionMixin:
    def get_required_action(self) -> str | None:  # noqa
        raise NotImplemented

    def get_permissions(self):
        self.required_action = self.get_required_action()  # noqa
        return super().get_permissions()  # noqa
