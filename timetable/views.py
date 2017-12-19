from django.shortcuts import render

# Create your views here.

def hello_world(request):
    context = {}
    return render(request, 'timetable.html', context);
