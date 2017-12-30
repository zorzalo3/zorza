from django import template

register = template.Library()

@register.filter
def hyphen_break(value):
    return str(value).replace('-', '-<wbr>')
