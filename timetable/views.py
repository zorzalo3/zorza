from django.shortcuts import render

# Create your views here.

def hello_world(request):
    context = {}
    return render(request, 'timetable.html', context);

def show_default_timetable(request):
    pass

def show_class_timetable(request):
    pass

def show_groups_timetable(request):
    pass

def show_room_timetable(request):
    pass

def show_teacher_timetable(request):
    pass
