import locale
from datetime import datetime, date, timedelta
from collections import OrderedDict

from django.conf import settings
from django.db.models import Min, Max
from django.http import Http404
from django.core.serializers import serialize
from django.utils import timezone

from .models import *

days = settings.TIMETABLE_WEEKDAYS
day_ids = [x[0] for x in days]

def get_max_period():
    return Period.objects.aggregate(Max('number'))['number__max']

def get_min_period():
    return Period.objects.aggregate(Min('number'))['number__min']

def get_period_strings(periods):
    return {period.number: str(period) for period in periods}

def get_display_context():
    context = {
        'days': days,
        'todays_periods_json': serialize('json', get_todays_periods()),
        'utc_offset': get_utc_offset(),
    }
    context.update(get_events())
    return context

def get_timetable_context(lessons):
    default_periods = Period.objects.filter(schedule__is_default=True)
    if not default_periods:
        raise Http404('No default timetable or periods')

    lessons = lessons.select_related('teacher', 'group', 'room', 'subject')

    periods = [period.number for period in default_periods]
    period_strs = get_period_strings(default_periods)

    # TODO: a cleaner way to pass period str to the template while using
    #       period number as key?
    table = OrderedDict()
    for period in periods:
        table[period] = (period_strs[period], OrderedDict())
        for day_number, day_string in days:
            table[period][1][day_number] = []

    for lesson in lessons:
        # Will throw exception if lesson.weekday not in days
        table[lesson.period][1][lesson.weekday].append(lesson)

    teachers = Teacher.objects.all().values()
    teachers = sorted(teachers, key=lambda t:
        locale.strxfrm(t['last_name']+t['first_name']))
        # Sort considering system locale

    context = {
        'table': table,
        'class_list': Class.objects.all().values(),
        'teacher_list': teachers,
        'room_list': Room.objects.all().values(),
        'timetable_version': settings.TIMETABLE_VERSION,
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
                            .select_related('teacher', 'substitute') \
                            .order_by('date', 'teacher', 'period'),
        'absences': Absence.objects.filter(**filter_kwargs) \
                            .order_by('date', 'group', 'period'),
        'reservations': Reservation.objects.filter(**filter_kwargs) \
                            .select_related('teacher', 'room') \
                            .order_by('date', 'period'),
        'dayplans': DayPlan.objects.filter(**filter_kwargs),
    }

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
        if any(weekday == day_number for day_number, day_string in days):
            schedule = Schedule.objects.get(is_default=True)
        else:
            return []
    return schedule.period_set.all()

def get_todays_periods():
    return get_days_periods(date.today())

def get_schedules_table():
    all_periods = Period.objects.all().prefetch_related('schedule')
    min_max = all_periods.aggregate(Min('number'), Max('number'))
    period_range = range(min_max['number__min'], min_max['number__max']+1)
    schedules = {period.schedule for period in all_periods}

    table = OrderedDict()
    for period in period_range:
        table[period] = OrderedDict()
        for schedule in schedules:
            table[period][schedule] = ''

    for period in all_periods:
        table[period.number][period.schedule] = str(period)

    context = {
        'schedules': schedules,
        'table': table,
    }
    context.update(get_display_context())
    return context;

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
