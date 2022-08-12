from django import template

register = template.Library()


@register.filter
def addclass(field, css):
    """Создаем фильтр для указания CSS классов."""
    return field.as_widget(attrs={'class': css})
