from django.contrib import admin
from django_celery_results.admin import GroupResultAdmin, TaskResultAdmin
from django_celery_results.models import GroupResult, TaskResult
from unfold.admin import ModelAdmin

# Celery
admin.site.unregister(GroupResult)
admin.site.unregister(TaskResult)


@admin.register(TaskResult)
class TaskResultAdmin(TaskResultAdmin, ModelAdmin):  # type: ignore[no-redef]
    pass


@admin.register(GroupResult)
class GroupResultAdmin(GroupResultAdmin, ModelAdmin):  # type: ignore[no-redef]
    pass
