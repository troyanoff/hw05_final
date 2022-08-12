from django.views.generic.base import TemplateView


class AboutAuthorViews(TemplateView):
    """Вывод статичного шаблона "Об авторе"."""

    template_name = 'about/author.html'


class AboutTechView(TemplateView):
    """Вывод статичного шаблона "Технологии"."""

    template_name = 'about/tech.html'
