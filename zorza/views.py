from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.conf import settings

@never_cache
@login_required
def manage(request):
    context = {
        'cache_time': int(settings.CACHE_MIDDLEWARE_SECONDS/60),
        'csv_enabled': bool(settings.TIMETABLE_CSV_HEADER),
    }
    return render(request, 'management.html', context)

