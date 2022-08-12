import datetime


def year(request):
    """Добавляет переменную с текущим годом."""
    date_today = datetime.date.today()

    return {
        'year': date_today.year
    }
