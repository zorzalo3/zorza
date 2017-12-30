from itertools import groupby
from django.shortcuts import render, get_object_or_404
from django.http import Http404
from django.conf import settings
from .models import *

days = settings.TIMETABLE_WEEKDAYS

def show_default_timetable(request):
    pass

def show_class_timetable(request):
    pass

def show_groups_timetable(request, group_ids):
    try:
        group_ids = {int(n) for n in group_ids.split(',')} # convert to set
    except:
        raise Http404

    groups = [get_object_or_404(Group, pk=n) for n in group_ids]
    lessons = Lesson.objects.filter(group__in=group_ids)
    periods = {lesson.period for lesson in lessons}
    table = {period: {day[0]: [] for day in days} for period in periods}
    for lesson in lessons:
        # Will throw exception if lesson.weekday not in days
        table[lesson.period][lesson.weekday].append(lesson)

    context = {
        'days': days,
        'table': table,
    }
    return render(request, 'timetable.html', context)

def show_room_timetable(request):
    pass

def show_teacher_timetable(request):
    pass
