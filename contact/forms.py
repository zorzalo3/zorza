from django import forms
from .models import Message

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['sender', 'subject', 'content']
        widgets = {
            'sender': forms.EmailInput(attrs={'class': 'input-field'}),
            'subject': forms.TextInput(attrs={'class': 'input-field'}),
            'content': forms.Textarea(attrs={'class': 'input-field'}),
        }