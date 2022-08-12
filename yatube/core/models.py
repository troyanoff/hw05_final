from django.db import models


class UniversalModel(models.Model):
    """Модель с частыми полями для моделей."""

    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации',
    )

    class Meta:
        abstract = True
