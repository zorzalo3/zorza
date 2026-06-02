from calendar import weekday
from csv import DictReader
from itertools import groupby
from collections import OrderedDict
from datetime import date, datetime

from io import TextIOWrapper

from django.shortcuts import render, get_object_or_404, redirect
from django.http import Http404, HttpResponseRedirect, JsonResponse
from django.urls import resolve, reverse
from django.utils.translation import gettext as _
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_POST
from django.views.decorators.vary import vary_on_cookie
from django.views.decorators.cache import never_cache
from django.views.generic.edit import FormView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.conf import settings

from .models import *
from .utils import (get_teachers_by_substitutions_date, get_timetable_context, get_schedules_table, get_days_periods,
    get_events, get_display_context, get_teacher_by_name, serialize_lessons_for_js, serialize_data,
    clear_cache, get_last_update)
from .forms import *


@vary_on_cookie
def show_timetable(request):
    """Redirects to timetable given in GET parameter or in cookies"""
    class_ = request.GET.get('class')
    if class_:
        return HttpResponseRedirect(f'/timetable/class/{class_}/')

    teacher = request.GET.get('teacher')
    if teacher:
        return HttpResponseRedirect(f'/timetable/teacher/{teacher}/')

    room = request.GET.get('room')
    if room:
        return HttpResponseRedirect(f'/timetable/room/{room}/')

    user_default = request.COOKIES.get('timetable_default') # set in JS
    version = request.COOKIES.get('timetable_version')
    if user_default is None or str(version) != str(settings.TIMETABLE_VERSION):
        response = HttpResponseRedirect('/timetable/class/1/')
        response.delete_cookie('timetable_default', path='/timetable/')
        response.delete_cookie('timetable_version', path='/timetable/')
        return response
    return HttpResponseRedirect(user_default)

def show_class_timetable(request, class_id):
    class_ = get_object_or_404(Class, pk=class_id)
    all_groups = list(Group.objects.filter(classes=class_))

    # Handle ?groups=1,3 filter — SSR renders only the selected groups
    groups_param = request.GET.get('groups', '')
    if groups_param:
        try:
            selected_ids = set(int(x) for x in groups_param.split(','))
            selected_groups = [g for g in all_groups if g.id in selected_ids]
            if not selected_groups:
                selected_groups = all_groups
        except ValueError:
            selected_groups = all_groups
    else:
        selected_groups = all_groups

    lessons = Lesson.objects.filter(group__in=selected_groups)
    context = get_timetable_context(lessons)
    context['class'] = class_
    context['groups'] = selected_groups  # drives "relevant" highlight in substitutions

    # All lessons serialized for JS client-side filtering
    all_lessons = Lesson.objects.filter(group__in=all_groups).select_related(
        'teacher', 'group', 'room', 'subject'
    ).prefetch_related('group__classes')
    
    timetable_last_update = get_last_update()
    context['init_data_json'] = serialize_lessons_for_js(all_groups, all_lessons, selected_groups, last_update=timetable_last_update)

    return render(request, 'class_timetable.html', context)

def show_groups_timetable(request, group_ids):
    orig_ids = group_ids
    try:
        requested_ids = list(map(int, group_ids.split(',')))
    except ValueError:
        raise Http404

    groups = Group.objects.filter(pk__in=requested_ids)

    found_ids = [str(group.pk) for group in groups]

    if not found_ids:
        raise Http404

    if len(found_ids) != len(requested_ids):
        valid_ids_str = ','.join(found_ids)
        new_url = request.path.replace(orig_ids, valid_ids_str)
        return HttpResponseRedirect(new_url) # If some of the requested groups were not found, redirect to the same URL with only the valid group IDs.

    if len(requested_ids) > 1:
        # Experimental redirect to class timetable if all groups belong to the same class
        group_class_db = list(groups.values('id', 'name', 'classes'))
        group_classes = {}
        for group in group_class_db:
            if not group_classes.get(group['classes']):
                group_classes[group['classes']] = []
            group_classes[group['classes']].append(group['id'])

        redirect_url = None
        found_max = 0
        for key, value in group_classes.items():
            if len(value) == len(requested_ids):
                found_max += 1
                redirect_url = f"/timetable/class/{key}/?groups={orig_ids}"

        if found_max == 1 and redirect_url:
            return HttpResponseRedirect(redirect_url)

    lessons = Lesson.objects.filter(group__in=requested_ids)
    context = get_timetable_context(lessons)
    context['groups'] = groups
    timetable_last_update = get_last_update()
    context['init_data_json'] = serialize_data({'last_update': timetable_last_update})
    
    return render(request, 'group_timetable.html', context)

def show_room_timetable(request, room_id):
    room = get_object_or_404(Room, pk=room_id)
    lessons = Lesson.objects.filter(room=room).prefetch_related('group__classes')
    context = get_timetable_context(lessons)
    context['room'] = room
    timetable_last_update = get_last_update()
    context['init_data_json'] = serialize_data({'last_update': timetable_last_update})
    
    return render(request, 'room_timetable.html', context)

def show_teacher_timetable(request, teacher_id):
    teacher = get_object_or_404(Teacher, pk=teacher_id)
    lessons = Lesson.objects.filter(teacher=teacher).prefetch_related('group__classes')
    context = get_timetable_context(lessons)
    context['teacher'] = teacher
    context['timetable_teacher'] = teacher
    timetable_last_update = get_last_update()
    context['init_data_json'] = serialize_data({'last_update': timetable_last_update})
    
    return render(request, 'teacher_timetable.html', context)

def personalize(request, class_id):
    # Deprecated view. Left for backward compatibility
    context = dict()
    if request.POST:
        groups = request.POST.getlist('group-checkbox')
        if not groups:
            context['error'] = _('Select at least one group')
        else:
            url = reverse('groups_timetable', args=[','.join(groups)])
            return HttpResponseRedirect(url)
    class_ = get_object_or_404(Class, pk=class_id)
    groups = Group.objects.filter(classes=class_)
    context['class'] = class_
    context['groups'] = groups
    return render(request, 'personalization.html', context)

def show_schedules(request):
    context = get_schedules_table()
    return render(request, 'schedules.html', context)

class AddSubstitutionsView1(LoginRequiredMixin, PermissionRequiredMixin, FormView):
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
        if today.month == 2 and today.day == 29:
            # Check if next year is a leap year
            next_year = today.year + 1
            if next_year % 4 == 0 and (next_year % 100 != 0 or next_year % 400 == 0):
                # If next year is a leap year, set the date to February 29th
                end_date = date(next_year, 2, 29)
            else:
                # If next year is not a leap year, set the date to February 28th
                end_date = date(next_year, 2, 28)
        else:
            # For other dates, simply increment the year by 1
            end_date = date(today.year + 1, today.month, today.day)
        events = get_events(end_date=end_date)
        context['substitutions'] = events['substitutions']
        context['show_substitution_'] = True
        return context

@never_cache
@login_required
@permission_required('timetable.add_substitution', raise_exception=True)
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
    
    clear_cache()
    
    context = {
        'teacher': teacher,
        'formset': formset,
        'date': date,
    }
    return render(request, 'add_substitutions.html', context)

@never_cache
@login_required
@permission_required('timetable.add_dayplan', raise_exception=True)
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
    
    clear_cache()
    
    context = {'formset': formset}
    return render(request, 'edit_calendar.html', context)

def show_rooms(request, date, period):
    from datetime import timedelta as _timedelta
    date = parse_date(date)
    weekday = date.weekday()
    period = int(period)

    rooms = {room: None for room in Room.objects.all()}
    lessons = Lesson.objects.filter(weekday=weekday, period=period) \
        .select_related('room', 'teacher', 'group', 'subject')
    for lesson in lessons:
        rooms[lesson.room] = lesson

    substitutions = Substitution.objects.filter(date=date, lesson__period=period)
    for sub in substitutions:
        rooms[sub.lesson.room].substitute = sub.substitute

    date_range = []
    for delta in range(-7, 8):
        d = date + _timedelta(days=delta)
        date_range.append({
            'date': d,
            'is_weekend': d.weekday() >= 5,
            'is_current': d == date,
        })

    min_p = get_min_period()
    max_p = get_max_period()
    period_range = list(range(min_p, max_p + 1)) if min_p is not None and max_p is not None else []

    context = {
        'date': date,
        'period': period,
        'rooms': rooms,
        'date_range': date_range,
        'period_range': period_range,
    }
    return render(request, 'rooms.html', context)

class RoomsDatePeriodSelectView(FormView):
    """A form with date and period to be passed to show_rooms."""
    template_name = 'rooms_date_period_select.html'
    form_class = SelectDateAndPeriodForm

    def get(self, request, *args, **kwargs):
        return redirect('rooms', get_next_schoolday(), get_min_period() or 0)

    def form_valid(self, form):
        date = form.cleaned_data['date']
        period = form.cleaned_data['period']
        return redirect('rooms', date, period)

@never_cache
def display(request):
    context = get_display_context()
    return render(request, 'display.html', context)


# This is view that should expose DayPlan, Schedule and Period models
# in JSON format for use in automated bell system.
# It should be incorporated in zorza API if one would be implemented
@never_cache
def timetable_bell_api(request):

    days = settings.BELL_API_TIMESPAN

    if not days > 0:
        raise Http404()

    now = datetime.datetime.now()

    #make dictionary
    data = {}
    data['date'] = { 'year': now.year, 'month': now.month, 'day': now.day }
    data['time'] = { 'hour': now.hour, 'minute': now.minute, 'second': now.second }
    data['bells'] = []

    current_date = now.date()
    for a in range(days):
        times = []
        for t in get_days_periods(current_date):
            times.append([t.begin_time.hour,t.begin_time.minute])
            times.append([t.end_time.hour,t.end_time.minute])
        times.sort()
        data['bells'].append(times)
        current_date += datetime.timedelta(days=1)

    return JsonResponse(data)

@never_cache
def get_last_update_api(request):
    last_update = get_last_update()
    return JsonResponse({'last_update': last_update})

@login_required
@permission_required('timetable.add_substitution', raise_exception=True)
@require_POST
def delete_substitution(request, substitution_id):
    if request.POST:
        obj = get_object_or_404(Substitution, pk=substitution_id)
        obj.delete()
        return HttpResponseRedirect(reverse('add_substitutions1'))

class SubstitutionsImportView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    template_name = 'import_substitutions.html'
    form_class = SubstitutionsImportForm
    permission_required = 'timetable.add_substitution'
    raise_exception = True
    
    def form_valid(self,form):
        csv_file = TextIOWrapper(
            form.cleaned_data['file'],
            encoding=settings.TIMETABLE_CSV_ENCODING)
        reader = DictReader(
            csv_file, skipinitialspace=True,
            delimiter=settings.TIMETABLE_CSV_DELIMITER)
        HEADER = settings.TIMETABLE_CSV_HEADER
        context = {
            'rows_failed': 0,
            'rows_added': 0,
            'rows_updated': 0,
            'substitutions': [],
            'errors': [],
        }
        for row in reader:
            try:
                #sub_date = parse_date(row[HEADER['date']])
                sub_date = parse_date(row[HEADER['date']].split()[0])
                tname = row[HEADER['teacher']]
                teacher = (get_teacher_by_name(tname, False) or
                        get_teacher_by_name(tname, True))
                lesson = Lesson.objects.get(
                        weekday=sub_date.weekday(),
                        period=int(row[HEADER['period']]),
                        teacher=teacher)
                sname = row[HEADER['substitute']]
                substitute = (get_teacher_by_name(sname, False) or
                        get_teacher_by_name(sname, True))

                obj, created = Substitution.objects.update_or_create(
                        date=sub_date, lesson=lesson,
                        defaults={'substitute': substitute})
                context['substitutions'].append(obj)
                if created:
                    context['rows_added'] += 1
                else:
                    context['rows_updated'] += 1
            except Exception as e:
                if ''.join(filter(None, row.values())) == '':
                    # Blank line
                    continue
                context['rows_failed'] += 1
                context['errors'].append(row)
        
        clear_cache()
        
        return render(self.request, 'csv_import_success.html', context)

@never_cache
def show_substitutions(request, date, teacher_ids):
    context = dict()
    try:
        teacher_ids = [int(n) for n in teacher_ids.split(',')]
    except:
        raise Http404
    date = parse_date(date)
    teachers = Teacher.objects.filter(pk__in=teacher_ids)
    if len(teacher_ids) != len(teachers):
        raise Http404
    substitutions = Substitution.objects.filter(date=date, lesson__teacher__in=teachers).order_by('date', 'lesson__teacher', 'lesson__period')
    context.update(get_timetable_context(Lesson.objects.filter(teacher__in=teachers)))
    context['substitutions'] = substitutions
    context['date'] = 'date'
    return render(request, 'show_substitutions_to_print.html', context)

class AddReservationView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    template_name = 'add_reservation.html'
    form_class = AddReservationForm
    permission_required = 'timetable.add_reservation'
    
    def form_valid(self, form):
        date = form.cleaned_data['date']
        period = form.cleaned_data['period']
        teacher = form.cleaned_data['teacher']
        room = form.cleaned_data['room']
        reservation = Reservation(date=date, period_number=period, teacher=teacher, room=room)
        reservation.save()
        return redirect('add_reservation')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(get_timetable_context(Lesson.objects.filter(room__in=Room.objects.filter(reservation__isnull=False).distinct())))
        context['show_reservation_delete'] = True
        
        clear_cache()
        return context

class AddAbsenceView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    template_name = 'add_absence.html'
    form_class = AddAbsenceForm
    permission_required = 'timetable.add_absence'
    
    def form_valid(self, form):
        date = form.cleaned_data['date']
        start_period = form.cleaned_data['start_period']
        end_period = form.cleaned_data['end_period']
        reason = form.cleaned_data['reason']
        group = form.cleaned_data['group']
        for period in range(start_period, end_period+1):
            absence = Absence(date=date, period_number=period, reason=reason, group=group)
            absence.save()
        return redirect('add_absence')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(get_timetable_context(Lesson.objects.filter(group__in=Group.objects.filter(absence__isnull=False).distinct())))
        context['show_absence_delete'] = True
        return context
    

class PrintSubstitutionsView1(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    permission_required = 'timetable.print_substitution'
    template_name = 'print_substitutions1.html'
    form_class = SelectDateForm
    
    def form_valid(self, form):
        date = form.cleaned_data['date']
        return redirect('print_substitutions2', str(date))
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = date.today()
        if today.month == 2 and today.day == 29:
            # Check if next year is a leap year
            next_year = today.year + 1
            if next_year % 4 == 0 and (next_year % 100 != 0 or next_year % 400 == 0):
                # If next year is a leap year, set the date to February 29th
                end_date = date(next_year, 2, 29)
            else:
                # If next year is not a leap year, set the date to February 28th
                end_date = date(next_year, 2, 28)
        else:
            # For other dates, simply increment the year by 1
            end_date = date(today.year + 1, today.month, today.day)
        events = get_events(end_date=end_date)
        context['substitutions'] = events['substitutions']
        return context

@never_cache
@login_required
@permission_required('timetable.print_substitutions', raise_exception=True)
def print_substitution2(request, date):
    context = dict()
    date = parse_date(date)
    if request.method == 'POST':
        teachers = request.POST.getlist('teacher-checkbox')
        if not teachers:
            context['error'] = _('Select at least one teacher')
        else:
            return redirect('show_substitutions_as_html', date, ','.join(teachers))
    teachers = get_teachers_by_substitutions_date(date)
    context['teachers'] = teachers
    context['date'] = date
    if len(teachers) < 1: 
        return render(request, 'show_substitutions_to_print.html', context)
    return render(request, 'print_substitutions2.html', context)

@login_required
@permission_required('timetable.add_reservation', raise_exception=True)
@require_POST
def delete_reservation(request, reservation_id):
    if request.POST:
        res = get_object_or_404(Reservation, pk=reservation_id)
        res.delete()
        
        clear_cache()
        return HttpResponseRedirect(reverse('add_reservation'))

@login_required
@permission_required('timetable.add_absence', raise_exception=True)
@require_POST
def delete_absence(request, absence_id):
    # Removes all absences with the same group and date as the given one
    if request.POST:
        given_abs = get_object_or_404(Absence, pk=absence_id)
        abs = Absence.objects.filter(group=given_abs.group, date=given_abs.date)
        abs.delete()
        
        clear_cache()
        return HttpResponseRedirect(reverse('add_absence'))
