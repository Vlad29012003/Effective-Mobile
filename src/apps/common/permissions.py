from rest_framework.permissions import IsAuthenticated


class ActionPermissionBase(IsAuthenticated):
    """Base permission class that checks for user action permission."""

    def get_required_action(self, view):
        required_action = getattr(view, "required_action", None)
        return required_action

    def get_app_label(self, view, obj=None):
        if obj is not None:
            return obj._meta.app_label  # noqa

        if hasattr(view, "queryset") and hasattr(view.queryset, "model"):
            return view.queryset.model._meta.app_label  # noqa

        if hasattr(view, "serializer_class"):
            model = getattr(view.serializer_class.Meta, "model", None)
            if model:
                return model._meta.app_label  # noqa

        return None

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False

        required_action = self.get_required_action(view)
        if not required_action:
            return True

        app_label = self.get_app_label(view)
        if not app_label:
            return False

        perm_string = f"{app_label}.{required_action}"
        return request.user.has_perm(perm_string)

    def has_object_permission(self, request, view, obj):
        if not super().has_object_permission(request, view, obj):
            return False

        required_action = self.get_required_action(view)
        if not required_action:
            return True

        app_label = self.get_app_label(view, obj)
        if not app_label:
            return False

        perm_string = f"{app_label}.{required_action}"
        return request.user.has_perm(perm_string)
