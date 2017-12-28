from itertools import groupby
from django.shortcuts import render, get_object_or_404
from django.http import Http404
from .models import *

# Create your views here.

def hello_world(request):
    context = {}
    return render(request, 'timetable.html', context);

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
    print(lessons)
    days = {l.weekday: str(l.get_weekday_display()) for l in lessons}
    lessons = sorted(lessons, key=lambda x: x.period)
    periods = {k:g for k, g in groupby(lessons, key=lambda x: x.period)}
    print(periods)
    context = {
        'days': days,
        'periods': periods,
    }
    return render(request, 'timetable.html', context)

def show_room_timetable(request):
    pass

def show_teacher_timetable(request):
    pass
