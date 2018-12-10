from datetime import date, timedelta
from django.core.management.base import BaseCommand
from timetable.models import *

class Command(BaseCommand):
    help = 'Removes substitutions, absences, reservations, and dayplans older than two weeks'

    def handle(self, *args, **options):
        past = date.today() - timedelta(days=14)
        for model in [Substitution, Absence, Reservation, DayPlan]:
            model.objects.filter(date__lt=past).delete()
