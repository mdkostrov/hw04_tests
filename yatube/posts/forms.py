from django import forms

from .models import Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group')
        help_texts = {
            'group': ('Выберите группу (необязательно)'),
            'text': ('Введите текст поста'),
        }
