from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Comment, Post


class CommentForm(forms.ModelForm):
    """Определение формы для создания комментариев."""

    class Meta:
        model = Comment
        fields = ('text', )
        help_texts = {
            'text': _('Оставьте ваш комментарий'),
        }
        widgets = {
            'text': forms.Textarea(attrs={'cols': 40, 'rows': 10}),
        }

        def clean_text(self):
            text = self.cleaned_data['text']
            if text is None:
                raise forms.ValidationError(
                    'Чтобы оставить комментарий, заполните это поле.'
                )
            return text


class PostForm(forms.ModelForm):
    """Определение формы для создания и изменения постов."""

    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        help_texts = {
            'text': _('Текст нового поста'),
            'group': _('Группа, к которой будет относиться пост'),
        }
        widgets = {
            'text': forms.Textarea(attrs={'cols': 20, 'rows': 10}),
        }

        def clean_text(self):
            text = self.cleaned_data['text']
            if text is None:
                raise forms.ValidationError(
                    'Чтобы сохранить пост, заполните это поле.'
                )
            return text
