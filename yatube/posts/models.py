from django.db import models
from django.contrib.auth import get_user_model

from core.models import UniversalModel

User = get_user_model()


class Follow(models.Model):
    """Определение модели системы подписок."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор',
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'


class Group(models.Model):
    """Определение модели Group и ее полей."""

    title = models.CharField(
        max_length=200,
        verbose_name='Название группы',
    )
    slug = models.SlugField(
        unique=True,
        verbose_name='Уникальное обозначение группы',
    )
    description = models.TextField(verbose_name='Описание группы')

    class Meta:
        verbose_name = 'Группа'
        verbose_name_plural = 'Группы'

    def __str__(self):
        """Вывод названия группы."""

        return self.title


class Post(UniversalModel):
    """Определение модели Post и ее полей."""

    text = models.TextField(verbose_name='Текст публикации')
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор публикации',
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        related_name='posts',
        blank=True,
        null=True,
        verbose_name='Группа',
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True
    )

    class Meta:
        ordering = ('-pub_date', )
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'

    def __str__(self):
        """Вывод содержания поста."""

        return self.text[:15]


class Comment(UniversalModel):
    """Определение подели комментариев."""

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор комментария'
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Комментируемый пост'
    )
    text = models.TextField(
        verbose_name='Текст комментария'
    )

    class Meta:
        ordering = ('-pub_date', )
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
