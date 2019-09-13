from django.test import TestCase, Client
from .models import *

class CategoryOrderTest(TestCase):

    def setUp(self):
        self.category = Category(name='cat')
        self.category.save()
        obj1 = Document(title='abcdef', category=self.category)
        obj1.save()
        obj2 = Document(title='zxcvbn', category=self.category)
        obj2.save()

    def test_title_ordering(self):
        self.category.order = 'title'
        self.category.save()
        c = Client()
        response = c.get('/documents/category/' + str(self.category.pk) + '/')
        items = list(response.context['items'])
        self.assertEquals(len(items), 2)
        self.assertTrue(items[0].title < items[1].title)

        self.category.order = '-title'
        self.category.save()
        response = c.get('/documents/category/' + str(self.category.pk) + '/')
        items = list(response.context['items'])
        self.assertEquals(len(items), 2)
        self.assertTrue(items[0].title > items[1].title)
