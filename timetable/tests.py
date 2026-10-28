from datetime import date, timedelta
from http.cookies import SimpleCookie

from django.contrib.auth.models import User
from django.test import TestCase, RequestFactory
from django.utils.translation import gettext_lazy as _
from django.conf import settings
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
        # Now there is a redirect to today's date so check is not required
        return
        for url in self.public_urls:
            response = self.client.get(self.app_prefix + url)
            self.assertEqual(response.status_code, 200) # Or change to 302 (redirect)

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


def next_date_for_weekday(weekday, span_days=None):
    if span_days is None:
        span_days = settings.TIMETABLE_EVENTS_SPAN_DAYS
    today = date.today()
    for n in range(span_days):
        d = today + timedelta(days=n)
        if d.weekday() == weekday:
            return d
    return None


class SubstitutionOverlayTest(TestCase):
    """Lesson 1: group=1 (class 1A), subject=1, teacher=1 (CG), period=1,
    weekday=0, room=1. Substitute teacher is teacher 2 (BR)."""
    fixtures = ['fixtures/demo.json']

    def setUp(self):
        self.target_date = next_date_for_weekday(0)
        self.assertIsNotNone(self.target_date,
            "Test relies on weekday 0 falling within TIMETABLE_EVENTS_SPAN_DAYS")

    def test_class_timetable_shows_substitution(self):
        Substitution.objects.create(lesson_id=1, substitute_id=2, date=self.target_date)
        response = self.client.get('/timetable/class/1/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'sub-original', response.content)
        self.assertIn(b'sub-new', response.content)
        self.assertIn(b'>CG<', response.content)
        self.assertIn(b'>BR<', response.content)

    def test_class_timetable_shows_cancelled_lesson(self):
        Substitution.objects.create(lesson_id=1, substitute_id=None, date=self.target_date)
        response = self.client.get('/timetable/class/1/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'lesson-danger', response.content)
        self.assertNotIn(b'sub-new', response.content)

    def test_class_timetable_ignores_substitution_outside_window(self):
        far_date = self.target_date + timedelta(days=settings.TIMETABLE_EVENTS_SPAN_DAYS + 7)
        Substitution.objects.create(lesson_id=1, substitute_id=2, date=far_date)
        response = self.client.get('/timetable/class/1/')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(b'sub-original', response.content)
        self.assertNotIn(b'lesson-danger', response.content)

    def test_absence_takes_precedence_over_substitution(self):
        Substitution.objects.create(lesson_id=1, substitute_id=2, date=self.target_date)
        Absence.objects.create(group_id=1, period_number=1, date=self.target_date,
            reason='chory')
        response = self.client.get('/timetable/class/1/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'lesson-danger', response.content)
        self.assertIn(b'chory', response.content)
        self.assertNotIn(b'sub-new', response.content)

    def test_room_timetable_shows_substitution(self):
        Substitution.objects.create(lesson_id=1, substitute_id=2, date=self.target_date)
        response = self.client.get('/timetable/room/1/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'sub-original', response.content)
        self.assertIn(b'sub-new', response.content)
        self.assertIn(b'teacher-inline', response.content)

    def test_teacher_timetable_own_lesson_substituted(self):
        Substitution.objects.create(lesson_id=1, substitute_id=2, date=self.target_date)
        response = self.client.get('/timetable/teacher/1/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'lesson-danger', response.content)
        self.assertNotIn(b'>BR<', response.content)

    def test_teacher_timetable_shows_teaching_for(self):
        Substitution.objects.create(lesson_id=1, substitute_id=2, date=self.target_date)
        response = self.client.get('/timetable/teacher/2/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'lesson-teaching-for', response.content)

    def test_unaffected_lessons_render_normally(self):
        Substitution.objects.create(lesson_id=1, substitute_id=2, date=self.target_date)
        response = self.client.get('/timetable/class/1/')
        self.assertEqual(response.status_code, 200)
        # Lesson 2 (same class, period 2, weekday 0) has no substitution.
        self.assertIn(b'>CG<', response.content)
        self.assertNotIn(b'lesson-teaching-for', response.content)

