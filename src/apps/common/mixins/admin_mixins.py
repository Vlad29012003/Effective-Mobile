from django.contrib import messages
from django.contrib.admin.utils import unquote
from django.http import HttpResponseRedirect
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from unfold.admin import ModelAdmin


class WarnUnsavedFormMixin:
    warn_unsaved_form = True


class SoftDeleteAdminMixin(ModelAdmin, WarnUnsavedFormMixin):
    """
    Mixin providing soft-delete functionality:
    marks objects as deleted by setting `deleted_at` instead of hard deletion.
    """

    def delete_view(self, request, object_id, extra_context=None):
        obj = self.get_object(request, unquote(object_id))

        if obj and getattr(obj, "deleted_at", None):
            self.message_user(
                request,
                _("Selected item has already been marked as deleted."),
                level=messages.ERROR,
            )
            return HttpResponseRedirect(request.META.get("HTTP_REFERER", "/"))

        return super().delete_view(request, object_id, extra_context)

    def delete_model(self, request, obj):
        obj.deleted_at = timezone.now()
        obj.save()

    def delete_queryset(self, request, queryset):
        for obj in queryset:
            if obj.deleted_at:
                continue

            obj.deleted_at = timezone.now()
            obj.save()
