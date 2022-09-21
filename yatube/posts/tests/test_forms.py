from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post

User = get_user_model()


class PostCreateEditFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user_author')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group,
            id='1'
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_post_creation_form(self):
        """
        При отправке валидной формы со страницы создания
        поста создаётся новая запись в базе данных.
        """
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Новый тестовый текст',
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse(
                'posts:profile', kwargs={'username': self.user.username}
            )
        )
        last_post = Post.objects.first()
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='Новый тестовый текст',
            ).exists()
        )
        self.assertEqual(last_post.text, 'Новый тестовый текст')
        self.assertEqual(last_post.group, None)
        self.assertEqual(last_post.author, self.user)

    def test_post_edit_form(self):
        """
        при отправке валидной формы со страницы
        редактирования поста происходит изменение
        поста с post_id в базе данных.
        """
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Измененный тестовый текст',
            'group': '',
        }
        response_post_edit = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        edited_post = Post.objects.filter(text='Измененный тестовый текст')
        response_group_list = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group.slug})
        )
        old_group_context = response_group_list.context['page_obj'].object_list
        self.assertRedirects(
            response_post_edit, reverse(
                'posts:post_detail', kwargs={'post_id': self.post.id}
            )
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(
            Post.objects.filter(
                text='Измененный тестовый текст',
                id='1'
            ).exists()
        )
        self.assertFalse(
            Post.objects.filter(
                text='Тестовый текст',
                id='1'
            ).exists()
        )
        self.assertNotIn(edited_post, old_group_context)
