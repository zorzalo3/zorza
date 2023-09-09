import datetime

from django.forms  import *
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import MinValueValidator, MaxValueValidator

from .models import *
from .utils import get_next_schoolday, get_min_period, get_max_period

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

        today = datetime.date.today()
        if date < today:
            raise ValidationError(_('The given date cannot be in the past'))
        if date >= datetime.date(today.year + 1, today.month, today.day):
            raise ValidationError(_('The given date must be within a year from now'))
        if not Lesson.objects.filter(teacher=teacher, weekday=date.weekday()):
            raise ValidationError(_('{} has no planned lessons on the given day.')
                    .format(teacher))
        return cleaned_data

class SubstitutionForm(ModelForm):
    def __init__(self, teachers, *args, **kwargs):
        super(SubstitutionForm, self).__init__(*args, **kwargs)
        self.choices = [('', _('-----')), ('null', _('cancelled'))]
        self.choices += [(str(t.pk), str(t)) for t in teachers]
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
            .filter(lesson__teacher=teacher, date=date) \
            .select_related() \
            .order_by('lesson__period')
        self.teacher = teacher
        self.teachers = Teacher.objects.all().exclude(id=teacher.id) # So as not to repeat queries
        self.date = date
        self.lessons = Lesson.objects \
            .filter(teacher=teacher, weekday=date.weekday()) \
            .select_related('teacher', 'group', 'room', 'subject') \
            .prefetch_related('group__classes') \
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
            obj = self.queryset.get(lesson__period=period)
        except ObjectDoesNotExist:
            obj = Substitution(lesson=self.lessons[i], date=self.date)
        form = SubstitutionForm(self.teachers, instance=obj, **defaults)
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Generate min and max value dynamically because Period objects may
        # change after server launch
        self.fields['period'] = IntegerField(label=_('Period number'),
            min_value=get_min_period(), max_value=get_max_period())

class GroupForm(ModelForm):
    class Meta:
        model = Group
        fields = '__all__'

    def clean(self):
        link_to_class = self.cleaned_data.get('link_to_class')
        classes = self.cleaned_data.get('classes')
        if link_to_class and classes.count() != 1:
            raise ValidationError('link_to_class required exactly one class')
        return self.cleaned_data

class SubstitutionsImportForm(Form):
    file = FileField(label=_('CSV file with substitutions'))
    def clean(self):
        cleaned_data = super().clean()
        #TODO check for encoding
        #TODO check for csv import errors
        return cleaned_data

class SelectDateForm(Form):
    date = Html5DateField(label=_('Date'), initial=get_next_schoolday)

class AddReservationForm(Form):
    date = Html5DateField(label=_('Date'), initial=get_next_schoolday)
    period = IntegerField(label=_('Period number'), min_value=get_min_period, max_value=get_max_period)
    teacher = ModelChoiceField(label=_('Teacher'), queryset=Teacher.objects.all())
    room = ModelChoiceField(label=_('Room'), queryset=Room.objects.all())

    def clean(self):
        cleaned_data = super().clean()
        period = cleaned_data.get('period')
        room = cleaned_data.get('room')
        if len(Reservation.objects.filter(period_number=period, room=room)):
            raise ValidationError(_('This room is already reserved during this period.'))
        return self.cleaned_data

class AddAbsenceForm(Form):
    date = Html5DateField(label=_('Date'), initial=get_next_schoolday)
    start_period = IntegerField(label=_('Start period'), min_value=get_min_period, max_value=get_max_period, required=False)
    end_period = IntegerField(label=_('End period'), min_value=get_min_period, max_value=get_max_period, required=False)
    is_whole_day = BooleanField(label=_('Whole day'), required=False)
    reason = CharField(label=_('Reason'), max_length=40, required=False)
    group = ModelChoiceField(label=_('Group'), queryset=Group.objects.all())
    
    def clean(self):
        cleaned_data = super().clean()
        is_whole_day = cleaned_data.get('is_whole_day')
        start_period = cleaned_data.get('start_period')
        end_period = cleaned_data.get('end_period')
        
        if is_whole_day:
            cleaned_data['start_period'] = get_min_period()
            cleaned_data['end_period'] = get_max_period()
        elif not is_whole_day and (start_period is None or end_period is None):
            raise ValidationError(_('Provide initial and final period.'))
        elif start_period > end_period:
            raise ValidationError(_('The initial period cannot be later than the final period.'))    
        
        return self.cleaned_data
