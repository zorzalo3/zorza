import json
import locale
import time
from datetime import datetime, date, timedelta
from collections import OrderedDict

from django.conf import settings
from django.db.models import Min, Max
from django.http import Http404
from django.core.serializers import serialize
from django.core.cache import cache
from django.utils import timezone

from .models import *

def days():
    return settings.TIMETABLE_WEEKDAYS

def day_ids():
    return [x[0] for x in days()]

def get_max_period():
    return Period.objects.aggregate(Max('number'))['number__max']

def get_min_period():
    return Period.objects.aggregate(Min('number'))['number__min']

def get_period_strings(periods):
    return {period.number: str(period) for period in periods}

def clear_cache():
    cache.clear()
    cache.set('last_update', time.time(), None)

def get_last_update():
    return cache.get('last_update', 0)

def get_display_context():
    context = {
        'days': days(),
        'day_ids': day_ids(),
        'todays_periods_json': serialize('json', get_todays_periods()),
        'utc_offset': get_utc_offset(),
    }
    context.update(get_events())
    return context

def get_object_or_none(model, *args, **kwargs):
    """Uses get() to return an object, or returns None if the object does not exist.
    Argument model must has get() attr."""
    try:
        return model.objects.get(*args, **kwargs)
    except model.DoesNotExist:
        return None


def get_weekday_target_dates(span_days=None):
    """For each weekday, the nearest date on/after today within the span of days"""
    if span_days is None:
        span_days = settings.TIMETABLE_EVENTS_SPAN_DAYS
    today = date.today()
    target_dates = {}
    for n in range(span_days):
        d = today + timedelta(days=n)
        if d.weekday() not in target_dates:
            target_dates[d.weekday()] = d
    return target_dates

def apply_substitution_overlay(lessons):
    """Attaches `.overlay` (dict or None) to each Lesson, describing a
    substitution/cancellation/absence on its nearest upcoming occurrence."""
    lessons = list(lessons)
    for lesson in lessons:
        lesson.overlay = None
    if not lessons:
        return lessons

    target_dates = get_weekday_target_dates()
    dates = set(target_dates.values())
    lesson_by_id = {lesson.id: lesson for lesson in lessons}

    sub_by_lesson_id = {}
    substitutions = Substitution.objects.filter(
        lesson_id__in=lesson_by_id.keys(), date__in=dates
    ).select_related('substitute')
    for sub in substitutions:
        lesson = lesson_by_id.get(sub.lesson_id)
        if lesson is not None and target_dates.get(lesson.weekday) == sub.date:
            sub_by_lesson_id[sub.lesson_id] = sub

    group_ids = {lesson.group_id for lesson in lessons}
    absence_by_group_period = {}
    absences = Absence.objects.filter(group_id__in=group_ids, date__in=dates)
    for absence in absences:
        absence_by_group_period[(absence.group_id, absence.period_number)] = absence

    for lesson in lessons:
        target_date = target_dates.get(lesson.weekday)
        if target_date is None:
            continue
        absence = absence_by_group_period.get((lesson.group_id, lesson.period))
        if absence is not None and absence.date == target_date:
            lesson.overlay = {'kind': 'absence', 'reason': absence.reason}
            continue
        sub = sub_by_lesson_id.get(lesson.id)
        if sub is not None:
            if sub.substitute_id is None:
                lesson.overlay = {'kind': 'cancelled'}
            else:
                lesson.overlay = {'kind': 'substituted', 'substitute': sub.substitute}
    return lessons

def get_teaching_for_entries(teacher):  
    target_dates = get_weekday_target_dates()
    dates = set(target_dates.values())
    substitutions = Substitution.objects.filter(
        substitute=teacher, date__in=dates
    ).select_related('lesson__group', 'lesson__subject', 'lesson__room', 'lesson__teacher')

    entries = []
    for sub in substitutions:
        lesson = sub.lesson
        if target_dates.get(lesson.weekday) == sub.date:
            lesson.overlay = {'kind': 'teaching_for', 'original_teacher': lesson.teacher}
            entries.append(lesson)
    return entries

def serialize_overlay_for_js(overlay):
    if not overlay:
        return None
    result = {'kind': overlay['kind']}
    if overlay['kind'] == 'substituted':
        substitute = overlay['substitute']
        result['substitute'] = {
            'id': substitute.id,
            'initials': substitute.initials,
            'full_name': substitute.full_name,
        }
    elif overlay['kind'] == 'absence':
        result['reason'] = overlay.get('reason') or ''
    return result

def get_timetable_context(lessons):
    default_periods = Period.objects.filter(schedule__is_default=True)
    if not default_periods:
        raise Http404('No default timetable or periods')

    lessons = apply_substitution_overlay(lessons.select_related('teacher', 'group', 'room', 'subject'))

    # TODO: a cleaner way to pass period str to the template while using
    #       period number as key?
    periods = [period.number for period in default_periods]
    period_strs = get_period_strings(default_periods)

    alt_dayplan = get_object_or_none(DayPlan, date=date.today(), schedule__is_default=None)
    table = OrderedDict()
    for period in periods:
        table[period] = (period_strs[period], OrderedDict())
        if alt_dayplan is not None and alt_dayplan.schedule is not None:
            # Alternative schedule exists and and these are not cancelled nor default lessons
            alt_period = get_object_or_none(Period, number=period, schedule=alt_dayplan.schedule)
            table[period] = table[period] + (alt_period if alt_period is not None else '',)
        elif alt_dayplan is not None and alt_dayplan.schedule is None:
            # Alternative schedule exists and and these ARE cancelled lessons
            table[period] = table[period] + ('',)

        for day_number, day_string in days():
            table[period][1][day_number] = []

    for lesson in lessons:
        # Will throw exception if lesson.weekday not in days
        table[lesson.period][1][lesson.weekday].append(lesson)

    teachers = Teacher.objects.all().values()
    teachers = sorted(teachers, key=lambda t:
    locale.strxfrm(t['last_name'] + t['first_name']))
    # Sort considering system locale

    context = {
        'table': table,
        'class_list': Class.objects.all().values(),
        'teacher_list': teachers,
        'room_list': Room.objects.all().values(),
        'timetable_version': settings.TIMETABLE_VERSION,
        'subject_list_json': json.dumps(get_subject_list(table)),
    }
    context.update(get_display_context())

    return context

EVENTS_SPAN_DAYS = settings.TIMETABLE_EVENTS_SPAN_DAYS
EVENTS_SPAN = timedelta(days=EVENTS_SPAN_DAYS)

def get_date_filter_kwargs(begin_date=None, end_date=None):
    if begin_date is None:
        begin_date = date.today()
    if end_date is None:
        end_date = begin_date+EVENTS_SPAN

    return {
        'date__gte': begin_date,
        'date__lt': end_date,
    }


def get_events(begin_date=None, end_date=None):
    filter_kwargs = get_date_filter_kwargs(begin_date, end_date)

    events = {
        'substitutions': Substitution.objects.filter(**filter_kwargs) \
                            .select_related('lesson', 'lesson__room',
                                'lesson__teacher', 'lesson__subject',
                                'lesson__group', 'substitute') \
                            .order_by('date', 'lesson__teacher', 'lesson__period'),
        'absences': Absence.objects.filter(**filter_kwargs) \
                            .order_by('date', 'group', 'period_number'),
        'reservations': Reservation.objects.filter(**filter_kwargs) \
                            .select_related('teacher', 'room') \
                            .order_by('date', 'period_number'),
        'dayplans': DayPlan.objects.filter(**filter_kwargs) \
                            .select_related('schedule')
                            .order_by('date', 'schedule'),
    }
    default = Schedule.objects.get(is_default=True)
    schedule_by_date = dict()
    for n in range((filter_kwargs['date__lt']-filter_kwargs['date__gte']).days):
        date = filter_kwargs['date__gte'] + timedelta(days=n)
        schedule_by_date[date] = default if date.weekday() in day_ids() else None

    for dayplan in events['dayplans']:
        schedule_by_date[dayplan.date] = dayplan.schedule

    period_strs = dict()
    for schedule in Schedule.objects.all():
        period_strs[schedule.id] = dict()

    for period in Period.objects.all():
        period_strs[period.schedule_id][period.number] = str(period)

    for sub in events['substitutions']:
        schedule = schedule_by_date[sub.date]
        if schedule == None:
            sub.period_str = ''
        else:
            sub.period_str = period_strs[schedule.id].get(sub.lesson.period, '')

    return events

def get_days_periods(date):
    try:
        dayplan = DayPlan.objects.get(date=date)
        # If lessons are cancelled that day, return an empty list
        if dayplan.schedule is None:
            return []
        else:
            schedule = dayplan.schedule
    except:
        weekday = date.weekday()
        # if no dayplan for that day and it's a working day
        if any(weekday == day_number for day_number, day_string in days()):
            schedule = Schedule.objects.get(is_default=True)
        else:
            return []
    return schedule.period_set.all()

def get_todays_periods():
    return get_days_periods(date.today())

def get_schedules_table():
    all_periods = Period.objects.all().select_related('schedule')
    schedules = {period.schedule for period in all_periods}
    default = next(schedule for schedule in schedules if schedule.is_default)

    table = OrderedDict()

    for period in default.period_set.all():
        table[period.number] = OrderedDict()
        for schedule in schedules:
            table[period.number][schedule] = ''

    for period in all_periods:
        table[period.number][period.schedule] = str(period)

    context = get_display_context()
    active = None # Today's schedule
    first = context['dayplans'].first() # The only dayplan which could be today
    if first and first.is_today:
        active = first.schedule
    elif date.today().weekday() in context['day_ids']:
        active = default

    context['active'] = active
    context['schedules'] = schedules
    context['table'] = table
    return context

def get_utc_offset():
    """Returns difference from UTC in minutes.
    Compatible with JS Date.getTimezoneOffset"""
    tz = timezone.get_default_timezone()
    now = timezone.make_aware(datetime.now(), tz)
    return -int(now.utcoffset().seconds / 60)

def get_period_str(period, date):
    periods = get_days_periods(date)
    try:
        return periods.get(number=period)
    except:
        return ''

def get_next_schoolday():
    """Returns the date of the next schoolday.
    Returns today if no such day in the upcoming EVENTS_SPAN_DAYS days"""
    today = date.today()
    # Generate considered dates
    dates = [(today + timedelta(days=n)) for n in range(EVENTS_SPAN_DAYS)]

    for day in dates:
        periods = get_days_periods(day)
        if not periods:
            continue
        if day > today or datetime.now().time() < periods.first().begin_time:
            return day
    return today

def get_teacher_by_name(full_name, surname_first=False):
    name1, name2 = full_name.split(maxsplit=1)
    if surname_first:
        name1, name2 = name2, name1
    qs = Teacher.objects.filter(first_name=name1, last_name=name2)
    if qs.exists():
        return qs.first()
    return None

def get_teachers_by_substitutions_date(date):
    substitutions = Substitution.objects.filter(date=date)
    teachers = []
    for substitution in substitutions:
        teachers.append(substitution.lesson.teacher)
    teachers = list(dict.fromkeys(teachers))
    teachers = sorted(teachers, key=lambda t:
        locale.strxfrm(t.last_name+t.first_name))
    return teachers


def serialize_lessons_for_js(all_groups, lessons, selected_groups, **kwargs):
    """Serialize lesson data for the JS group filter on the class timetable page."""
    lesson_list = []
    for lesson in lessons:
        item = {
            'period': lesson.period,
            'weekday': lesson.weekday,
            'teacher': {
                'id': lesson.teacher_id,
                'initials': lesson.teacher.initials,
                'full_name': lesson.teacher.full_name,
            },
            'subject': {
                'name': lesson.subject.name,
                'short_name': lesson.subject.short_name,
            },
            'room': {
                'id': lesson.room_id or 0,
                'name': lesson.room.name if lesson.room else '',
                'short_name': lesson.room.short_name if lesson.room else '',
            },
            'group': {
                'id': lesson.group_id,
                'name': lesson.group.name,
                'link_to_class': lesson.group.link_to_class,
            },
            'overlay': serialize_overlay_for_js(getattr(lesson, 'overlay', None)),
        }
        if lesson.group.link_to_class:
            first_class = lesson.group.classes.first()
            if first_class:
                item['class'] = {'id': first_class.id, 'name': first_class.name}
        lesson_list.append(item)
    
    final_dict = {
        'type': 'class',
        'lessons': lesson_list,
        'groups': [{'id': g.id, 'name': g.name} for g in all_groups],
        'selected_group_ids': [g.id for g in selected_groups],
    }
    
    for key, value in kwargs.items():
        final_dict[key] = value
    
    return json.dumps(final_dict, ensure_ascii=False)

def serialize_data(data: dict):
    """Serialize data for JS, converting date and time objects to strings."""
    return json.dumps(data, ensure_ascii=False)

def get_subject_list(table):
    """Extract unique subject short names from timetable."""
    subjects = []
    seen = set()
    for period, (period_str, hours_dict) in table.items():
        for day, lessons in hours_dict.items():
            for lesson in lessons:
                short = lesson.subject.short_name
                if short and short not in seen:
                    seen.add(short)
                    subjects.append(short)
    return subjects
