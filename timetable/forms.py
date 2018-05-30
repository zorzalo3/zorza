from django.forms  import *
from django.utils.translation import gettext_lazy as _

from .models import *
from .utils import get_next_schoolday

class Html5DateInput(DateInput):
    input_type = 'date'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.format = '%Y-%m-%d'

class Html5DateField(DateField):
    widget = Html5DateInput(format='%Y-%m-%d')

class SelectTeacherAndDateForm(Form):
    teacher = ModelChoiceField(label=_('Teacher'), queryset=Teacher.objects.all())
    date = DateField(
        label=_('Date'), initial=get_next_schoolday, widget=Html5DateInput)

class SubstitutionForm(ModelForm):
    class Meta:
        model = Substitution
        fields = ('period', 'substitute',)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['substitute'].empty_label = _('cancelled')

SubstitutionFormSet = modelformset_factory(
    Substitution, form=SubstitutionForm, extra=8, can_delete=True)

class DayPlanForm(ModelForm):
    class Meta:
        model = DayPlan
        fields = '__all__'
        field_classes = {
            'date': Html5DateField
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['schedule'].empty_label = _('cancelled')

DayPlanFormSet = modelformset_factory(DayPlan, form=DayPlanForm, extra=8)
