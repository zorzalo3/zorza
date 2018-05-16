from datetime import date

from django.forms  import *
from django.utils.translation import gettext_lazy as _

from .models import *
from .utils import get_next_schoolday

class SelectTeacherAndDateForm(Form):
    teacher = ModelChoiceField(label=_('Teacher'), queryset=Teacher.objects.all())
    date = DateField(label=_('Date'), initial=get_next_schoolday)

class SubstitutionForm(ModelForm):
    class Meta:
        model = Substitution
        fields = ('period', 'substitute',)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['substitute'].empty_label = _('cancelled')

SubstitutionFormSet = modelformset_factory(
    Substitution, form=SubstitutionForm, extra=8, can_delete=True)


DayPlanFormSet = modelformset_factory(
    DayPlan, fields='__all__', extra=8)
