from itertools import groupby
from django.shortcuts import render, get_object_or_404
from django.http import Http404, HttpResponseRedirect
from django.urls import resolve, reverse
from django.utils.translation import gettext as _
from django.views.decorators.vary import vary_on_cookie
from .models import *
from .utils import get_timetable_context


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
