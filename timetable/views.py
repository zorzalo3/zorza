from itertools import groupby
from django.shortcuts import render, get_object_or_404
from django.http import Http404
from .models import *
from .utils import get_timetable_context


def show_default_timetable(request):
    pass

def show_class_timetable(request, class_id):
    klass = get_object_or_404(Class, pk=class_id)
    groups = Group.objects.filter(classes=klass)
    lessons = Lesson.objects.filter(group__in=groups)
    context = get_timetable_context(lessons)
    context['class'] = klass
    return render(request, 'timetable.html', context)

def show_groups_timetable(request, group_ids):
    try:
        group_ids = {int(n) for n in group_ids.split(',')} # convert to set
    except:
        raise Http404

    groups = [get_object_or_404(Group, pk=n) for n in group_ids]
    lessons = Lesson.objects.filter(group__in=group_ids)
    context = get_timetable_context(lessons)
    context['groups'] = groups
    return render(request, 'timetable.html', context)

def show_room_timetable(request):
    pass

def show_teacher_timetable(request):
    pass
