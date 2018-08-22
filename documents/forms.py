from django.forms import *
from django.utils.translation import gettext_lazy as _

from .models import *

class WysiwygEditor(widgets.Textarea):
    template_name = "widgets/wysiwyg.html"
    class Media:
        css = {
            'all': ('medium-editor.min.css', 'medium-editor.flat.min.css')
        }
        js = ('medium-editor.min.js',)

class FileForm(ModelForm):
    category = ModelChoiceField(label=_('Category'), queryset=Category.objects.all(), required=False)
    class Meta:
        model = File
        fields = ('title', 'category', 'data')
        labels = {
            'title': _('Title'),
            'data': _('File'),
        }

class DocumentForm(ModelForm):
    category = ModelChoiceField(label=_('Category'), queryset=Category.objects.all(), required=False)
    class Meta:
        model = Document
        fields = ('title', 'category', 'content')
        labels = {
            'title': _('Title'),
            'content': _('Content'),
        }
        widgets = {
            'content': WysiwygEditor
        }
