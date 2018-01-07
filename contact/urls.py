from django.urls import path
from django.views.generic import TemplateView, CreateView

from .models import Message

urlpatterns = [
    path('', CreateView.as_view(model=Message, success_url='success/', fields='__all__'), name='contact'),
    path('success/', TemplateView.as_view(template_name='contact/success.html'), name='success'),
]
