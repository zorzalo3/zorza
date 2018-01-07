from django.db import models
from django.utils.translation import gettext_lazy as _

class Message(models.Model):
    sender = models.EmailField(_('Your email address'))
    subject = models.CharField(_('Subject'), max_length=100)
    content = models.TextField(_('Content'), max_length=1000)

    def __str__(self):
        return self.subject
