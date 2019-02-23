from datetime import date
from http.cookies import SimpleCookie

from django.contrib.auth.models import User
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

class TimetableStatusCodeTest(TestCase):
    fixtures = ['fixtures/demo.json']
    app_prefix = '/timetable'
    public_urls = [
        '/class/1/', '/room/1/', '/teacher/1/', '/groups/1,2/',
        '/personalize/1/', '/display/', '/rooms/', '/rooms/2018-12-31/1/',
    ]
    restricted_urls = [
        '/substitutions/add/', '/substitutions/add/1/2018-12-31/',
        '/calendar/edit/'
    ]
    def setUp(self):
        self.user = User.objects.create_user('user', password='secret')
        self.user.save()

    def test_public_status_ok(self):
        for url in self.public_urls:
            response = self.client.get(self.app_prefix + url)
            self.assertEqual(response.status_code, 200)

    def test_restricted_redirect(self):
        for url in self.restricted_urls:
            response = self.client.get(self.app_prefix + url)
            self.assertEqual(response.status_code, 302)

    def test_restricted_logged_in_redirect(self):
        self.client.force_login(self.user)
        for url in self.restricted_urls:
            response = self.client.get(self.app_prefix + url)
            self.assertEqual(response.status_code, 403)
        self.client.logout()

class DefaultTimetableTest(TestCase):
    fixtures = ['fixtures/demo.json']

    def test(self):
        fallback = '/timetable/class/1/'
        user_default = '/timetable/class/2/'
        cookie1 = SimpleCookie({'timetable_default': user_default})
        cookie1['timetable_default']['path'] = '/timetable/'
        self.client.cookies = cookie1

        with self.settings(TIMETABLE_VERSION=None):
            response = self.client.get('/timetable/')
            self.assertRedirects(response, user_default)

        with self.settings(TIMETABLE_VERSION='changed'):
            response = self.client.get('/timetable/')
            self.assertRedirects(response, fallback)

        cookie2 = SimpleCookie({
            'timetable_default': user_default,
            'timetable_version': 'changed'
        })
        self.client.cookies = cookie2

        with self.settings(TIMETABLE_VERSION='changed'):
            response = self.client.get('/timetable/')
            self.assertRedirects(response, user_default)

        with self.settings(TIMETABLE_VERSION='changedAgain'):
            response = self.client.get('/timetable/')
            self.assertRedirects(response, fallback)

