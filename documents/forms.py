from django.forms import *
from django.utils.translation import gettext_lazy as _

from .models import *

class FileForm(ModelForm):
    category = ModelChoiceField(queryset=Category.objects.all(), required=False)
    class Meta:
        model = File
        fields = ('title', 'category', 'data')

class DocumentForm(ModelForm):
    category = ModelChoiceField(queryset=Category.objects.all(), required=False)
    class Meta:
        model = Document
        fields = ('title', 'category', 'content')
