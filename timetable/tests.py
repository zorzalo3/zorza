from datetime import date

from django.test import TestCase, RequestFactory
from django.utils.translation import gettext_lazy as _
from .views import *
from .models import *


ALL_WEEKDAYS = (
    (0, _('Monday')),
    (1, _('Tuesday')),
    (2, _('Wednesday')),
    (3, _('Thursday')),
    (4, _('Friday')),
    (5, _('Saturday')),
    (6, _('Sunday')),
)

class ScheduleDefaultTest(TestCase):
    fixtures = ['fixtures/demo.json']

    def test_default_schedule(self):
        with self.settings(TIMETABLE_WEEKDAYS=ALL_WEEKDAYS):
            response = self.client.get('/timetable/schedules/')
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'class="highlight"', response.content)

    def test_no_schedule(self):
        with self.settings(TIMETABLE_WEEKDAYS=()):
            response = self.client.get('/timetable/schedules/')
            self.assertEqual(response.status_code, 200)
            self.assertNotIn(b'class="highlight"', response.content)


class ScheduleChangeTest(TestCase):
    fixtures = ['fixtures/demo.json']
    def setUp(self):
        obj = DayPlan(date=date.today(),
            schedule=Schedule.objects.exclude(is_default=True).first())
        obj.save()

    def test_weekday(self):
        with self.settings(TIMETABLE_WEEKDAYS=()):
            response = self.client.get('/timetable/schedules/')
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'class="highlight"', response.content)

    def test_weekend(self):
        with self.settings(TIMETABLE_WEEKDAYS=ALL_WEEKDAYS):
            response = self.client.get('/timetable/schedules/')
            self.assertEqual(response.status_code, 200)
            self.assertIn(b'class="highlight"', response.content)



