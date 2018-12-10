from itertools import groupby
from collections import OrderedDict
from datetime import date

from django.shortcuts import render, get_object_or_404, redirect
from django.http import Http404, HttpResponseRedirect
from django.urls import resolve, reverse
from django.utils.translation import gettext as _
from django.utils.dateparse import parse_date
from django.views.decorators.vary import vary_on_cookie
from django.views.decorators.cache import never_cache
from django.views.generic.edit import FormView
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.conf import settings

from .models import *
from .utils import (get_timetable_context, get_schedules_table, get_days_periods,
    get_substitutions, get_display_context)
from .forms import *


@vary_on_cookie
def show_default_timetable(request):
    default_url = request.COOKIES.get('timetable_default') # set in JS
    if default_url is None:
        return HttpResponseRedirect(reverse('class_timetable', args=[1]))
    view, args, kwargs = resolve(default_url)
    if view:
        return HttpResponseRedirect(default_url)

def show_class_timetable(request, class_id):
    klass = get_object_or_404(Class, pk=class_id)
    groups = Group.objects.filter(classes=klass)
    lessons = Lesson.objects.filter(group__in=groups)
    context = get_timetable_context(lessons)
    context['class'] = klass
    context['groups'] = groups
    return render(request, 'class_timetable.html', context)

def show_groups_timetable(request, group_ids):
    try:
        group_ids = {int(n) for n in group_ids.split(',')} # convert to set
    except:
        raise Http404

    groups = [get_object_or_404(Group, pk=n) for n in group_ids]
    lessons = Lesson.objects.filter(group__in=group_ids)
    context = get_timetable_context(lessons)
    context['groups'] = groups
    return render(request, 'group_timetable.html', context)

def show_room_timetable(request, room_id):
    room = get_object_or_404(Room, pk=room_id)
    lessons = Lesson.objects.filter(room=room)
    context = get_timetable_context(lessons)
    context['room'] = room
    return render(request, 'room_timetable.html', context)

def show_teacher_timetable(request, teacher_id):
    teacher = get_object_or_404(Teacher, pk=teacher_id)
    lessons = Lesson.objects.filter(teacher=teacher)
    context = get_timetable_context(lessons)
    context['teacher'] = teacher
    context['timetable_teacher'] = teacher
    return render(request, 'teacher_timetable.html', context)

def personalize(request, class_id):
    #TODO: switch to a Django form?
    context = dict()
    if request.POST:
        groups = request.POST.getlist('group-checkbox')
        if not groups:
            context['error'] = _('Select at least one group')
        else:
            url = reverse('groups_timetable', args=[','.join(groups)])
            return HttpResponseRedirect(url)
    klass = get_object_or_404(Class, pk=class_id)
    groups = Group.objects.filter(classes=klass)
    context['class'] = klass
    context['groups'] = groups
    return render(request, 'personalization.html', context)

def show_schedules(request):
    context = get_schedules_table()
    return render(request, 'schedules.html', context)

class AddSubstitutionsView1(PermissionRequiredMixin, FormView):
    """The first step to adding a substitution

    selects a teacher and a date to be passed into the second step
    """
    permission_required = 'timetable.add_substitution'
    template_name = 'teacher_and_date_select.html'
    form_class = SelectTeacherAndDateForm

    def form_valid(self, form):
        teacher = form.cleaned_data['teacher']
        date = form.cleaned_data['date']
        return redirect('add_substitutions2', teacher.pk, str(date))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = date.today()
        end_date = date(today.year + 1, today.month, today.day)
        context['substitutions'] = get_substitutions(end_date=end_date)
        context['show_substitution_delete'] = True
        return context

@never_cache
@permission_required('timetable.add_substitution')
def add_substitutions2(request, teacher_id, date):
    date = parse_date(date)
    teacher = get_object_or_404(Teacher, pk=teacher_id)

    if request.method == 'POST':
        formset = SubstitutionFormSet(teacher, date, request.POST)
        if formset.is_valid():
            formset.save()
            return HttpResponseRedirect(reverse('add_substitutions1'))
    else:
        formset = SubstitutionFormSet(teacher, date)

    context = {
        'teacher': teacher,
        'formset': formset,
        'date': date,
    }
    return render(request, 'add_substitutions.html', context)

@never_cache
@permission_required('timetable.add_dayplan')
def edit_calendar(request):
    qs = DayPlan.objects.filter(date__gte=date.today())
    if request.method == 'POST':
        formset = DayPlanFormSet(request.POST, queryset=qs)
        if formset.is_valid():
            formset.save()
            # Refresh the formset by refreshing the page
            return HttpResponseRedirect(request.path)
    else:
        formset = DayPlanFormSet(queryset=qs)
    context = {'formset': formset}
    return render(request, 'edit_calendar.html', context)

def show_rooms(request, date, period):
    date = parse_date(date)
    weekday = date.weekday()
    period = int(period)

    rooms = {room: None for room in Room.objects.all()}
    lessons = Lesson.objects.filter(weekday=weekday, period=period) \
        .select_related('room', 'teacher', 'group', 'subject')
    for lesson in lessons:
        rooms[lesson.room] = lesson

    substitutions = Substitution.objects.filter(date=date, period=period)
    for sub in substitutions:
        rooms[sub.room].substitute = sub.substitute

    context = {
        'date': date,
        'period': period,
        'rooms': rooms,
    }
    return render(request, 'rooms.html', context)

class RoomsDatePeriodSelectView(FormView):
    """A form with date and period to be passed to show_rooms."""
    template_name = 'rooms_date_period_select.html'
    form_class = SelectDateAndPeriodForm

    def form_valid(self, form):
        date = form.cleaned_data['date']
        period = form.cleaned_data['period']
        return redirect('rooms', date, period)

@never_cache
def display(request):
    context = get_display_context()
    return render(request, 'display.html', context)

@permission_required('timetable.add_substitution')
def delete_substitution(request, substitution_id):
    if request.POST:
        obj = get_object_or_404(Substitution, pk=substitution_id)
        obj.delete()
        return HttpResponseRedirect(reverse('add_substitutions1'))
