from django import template


register = template.Library()


@register.filter
def mul_10(value):
    try:
        return int(value) * 10
    except (TypeError, ValueError):
        return 0
