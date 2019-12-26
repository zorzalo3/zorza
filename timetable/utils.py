import locale
from datetime import datetime, date, timedelta
from collections import OrderedDict

from django.conf import settings
from django.db.models import Min, Max
from django.http import Http404
from django.core.serializers import serialize
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

def get_display_context():
    context = {
        'days': days(),
        'day_ids': day_ids(),
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
        for day_number, day_string in days():
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
                            .order_by('schedule', 'date'),
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

def get_teacher_by_name(full_name, surname_first=False):
    name1, name2 = full_name.split(maxsplit=1)
    if surname_first:
        name1, name2 = name2, name1
    qs = Teacher.objects.filter(first_name=name1, last_name=name2)
    if qs.exists():
        return qs.first()
    return None
