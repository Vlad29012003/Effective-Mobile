from django_celery_beat.admin import PeriodicTaskForm
from unfold.widgets import UnfoldAdminTextInputWidget

from apps.common.widgets import UnfoldTaskSelectWidget


class UnfoldPeriodicTaskForm(PeriodicTaskForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["task"].widget = UnfoldAdminTextInputWidget()
        self.fields["regtask"].widget = UnfoldTaskSelectWidget()
