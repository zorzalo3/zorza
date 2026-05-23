from django.urls import path
from django.views.generic import TemplateView, CreateView

from .forms import MessageForm

urlpatterns = [
    path('', CreateView.as_view(
        form_class=MessageForm,
        template_name='contact/message_form.html',
        success_url='success/',
    ), name='contact'),
    path('success/', TemplateView.as_view(template_name='contact/success.html'), name='success'),
]
