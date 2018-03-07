from django.db import models
from django.conf import settings
from tinymce.models import HTMLField

class Category(models.Model):
    name = models.CharField(max_length=50)
    parent = models.ForeignKey('self', null=True, blank=True,
                               on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class Item(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL,
                               on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    category = models.ForeignKey(Category, null=True, blank=True,
                                 on_delete=models.CASCADE)
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class File(Item):
    data = models.FileField(upload_to='documents/')

class Document(Item):
    content = HTMLField()
