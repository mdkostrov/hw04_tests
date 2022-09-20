from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()

POST_PREVIEW = 15


class Group(models.Model):
    title = models.CharField(max_length=200, verbose_name='Название группы')
    slug = models.SlugField(
        unique=True,
        verbose_name='Человекочитаемый URL группы'
    )
    description = models.TextField(verbose_name='Описание группы')

    def __str__(self) -> str:
        return f'{self.title}'


class Post(models.Model):
    text = models.TextField(
        verbose_name='Текст записи',
        help_text='Введите текст поста'
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор',
    )
    group = models.ForeignKey(
        Group,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='posts',
        verbose_name='Название группы',
        help_text='Группа, к которой будет относиться пост'
    )

    def __str__(self) -> str:
        return f'{self.text[:POST_PREVIEW]}'

    class Meta:
        ordering = ['-pub_date']
