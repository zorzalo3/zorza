from django.forms  import *
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist

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

    def clean(self):
        cleaned_data = super().clean()
        teacher = cleaned_data.get('teacher')
        date = cleaned_data.get('date')
        if not Lesson.objects.filter(teacher=teacher, weekday=date.weekday()):
            raise ValidationError(_('{} has no planned lessons on the given day.')
                    .format(teacher))
        return cleaned_data

class SubstitutionForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(SubstitutionForm, self).__init__(*args, **kwargs)
        self.choices = [('', _('-----')), ('null', _('cancelled'))]
        self.choices += [(str(t.pk), str(t)) for t in Teacher.objects.all()]
        self.fields['substitute'] = ChoiceField(choices=self.choices, required=False)
        if self.instance.substitute == None \
                and Substitution.objects.filter(pk=self.instance.pk).exists():
            self.initial['substitute'] = 'null'

    def clean_substitute(self):
        data = self.cleaned_data.get('substitute')
        choices = [i[0] for i in self.choices]
        self.to_delete = False
        if data in choices:
            if data == '':
                self.to_delete = True
                return None
            if data == 'null':
                return None
            else:
                return Teacher.objects.get(pk=data)
        else:
            raise ValidationError('Invalid choice')

    def save(self, commit=True):
        if self.to_delete:
            if self.instance.pk:
                self.instance.delete()
        else:
            super().save(commit)

    class Meta:
        model = Substitution
        fields = ['substitute']

class BaseSubstitutionFormSet(BaseModelFormSet):
    model = Substitution
    def __init__(self, teacher, date, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queryset = Substitution.objects \
            .filter(teacher=teacher, date=date) \
            .order_by('period')
        self.teacher = teacher
        self.date = date
        self.lessons = Lesson.objects \
            .filter(teacher=teacher, weekday=date.weekday()) \
            .order_by('period')

    def total_form_count(self):
        return len(self.lessons)

    def save(self):
        for form in self.forms:
            form.save()

    def _construct_form(self, i, **kwargs):
        defaults = {
            'auto_id': self.auto_id,
            'prefix': self.add_prefix(i),
            'error_class': self.error_class,
            'use_required_attribute': False,
        }
        if self.is_bound:
            defaults['data'] = self.data
        period = self.lessons[i].period
        try:
            obj = self.queryset.get(period=period)
        except ObjectDoesNotExist:
            obj = Substitution(teacher=self.teacher, period=period, date=self.date)
        form = SubstitutionForm(instance=obj, **defaults)
        form.lesson = self.lessons[i]
        return form

SubstitutionFormSet = formset_factory(Substitution, BaseSubstitutionFormSet, extra=0)


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

class SelectDateAndPeriodForm(Form):
    date = Html5DateField(label=_('Date'), initial=get_next_schoolday)
    period = IntegerField(label=_('Period'))
