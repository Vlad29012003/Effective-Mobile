from django_celery_beat.admin import TaskSelectWidget
from unfold.widgets import UnfoldAdminSelectWidget


class UnfoldTaskSelectWidget(UnfoldAdminSelectWidget, TaskSelectWidget):
    pass
