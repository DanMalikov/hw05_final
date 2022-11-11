from django import forms

from .models import Post, Comment


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        labels = {'group': 'Группа', 'text': 'Поле для ввода текста'}
        help_texts = {'group': 'Выбрать группу', 'text': 'Введите текст'}
        fields = (
            'text',
            'group',
            'image'
        )


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)
