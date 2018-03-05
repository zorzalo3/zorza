from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.mail import mail_admins

class Message(models.Model):
    sender = models.EmailField(_('Your email address'))
    subject = models.CharField(_('Subject'), max_length=100)
    content = models.TextField(_('Content'), max_length=1000)
    datetime = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.subject

    def save(self, *args, **kwargs):
        # If creating a new instance of Message
        if self.pk is None:
            message = '%s: \n\n%s' % (self.sender, self.content)
            mail_admins(self.subject, message)
        super().save(*args, **kwargs)

