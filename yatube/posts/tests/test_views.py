from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django import forms

from posts.models import Group, Post
from posts.views import POSTS_PER_PAGE

User = get_user_model()

TEST_POSTS_COUNT = 15


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Vasya')
        cls.group = Group.objects.create(
                        title='Тестовая группа',
                        slug='test-slug'
                    )
        cls.another_group = Group.objects.create(
                        title='Тестовая группа2',
                        slug='test-slug2'
                    )
        for test_post_id in range(TEST_POSTS_COUNT):
            Post.objects.create(
                text='Текст поста',
                author=cls.user,
                group=cls.group,
                id=str(test_post_id)
            )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_use_correct_template(self):
        """URL-адрес (namespace:name) использует соответствующий шаблон."""
        post = Post.objects.get(id=1)
        reverse_names_templates = {
            reverse('posts:index'):
                'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': self.group.slug}):
                'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': self.user.username}):
                'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': post.id}):
                'posts/post_detail.html',
            reverse('posts:post_create'):
                'posts/create_post.html',
            reverse('posts:post_edit', kwargs={'post_id': post.id}):
                'posts/create_post.html'
        }
        for reverse_name, template in reverse_names_templates.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_context(self):
        """На главную страницу передается правильный контекст"""
        last_posts = (
            Post.objects.all().order_by('-pub_date')[:POSTS_PER_PAGE]
        )
        response = self.authorized_client.get(reverse('posts:index'))
        context_obj = response.context.get('page_obj').object_list
        self.assertEqual(context_obj, list(last_posts))

    def test_group_list_page_context(self):
        """На страницу группы передается правильный контекст"""
        group_posts = (
            Post.objects.filter(group=self.group)
            .order_by('-pub_date')[:POSTS_PER_PAGE]
        )
        response = (
            self.authorized_client.
            get(reverse('posts:group_list', kwargs={'slug': self.group.slug}))
        )
        context_obj_page = response.context.get('page_obj').object_list
        context_obj_group = response.context['group']
        self.assertEqual(context_obj_page, list(group_posts))
        self.assertEqual(context_obj_group, self.group)

    def test_profile_page_context(self):
        """На страницу посты пользователя передается правильный контекст"""
        profile = (
            Post.objects.filter(author=self.user)
            .order_by('-pub_date')[:POSTS_PER_PAGE]
        )
        response = (
            self.authorized_client.
            get(reverse('posts:profile',
                kwargs={'username': (self.user.username)}))
        )
        context_obj = response.context.get('page_obj').object_list
        self.assertEqual(context_obj, list(profile))

    def test_post_detail_page_context(self):
        """
        На страницу детальной информации о
        посте передается правильный контекст
        """
        post_in_db = Post.objects.get(id=1)
        response = (
            self.authorized_client.
            get(reverse('posts:post_detail',
                kwargs={'post_id': post_in_db.id}))
        )
        post_in_context = response.context['post']
        self.assertEqual(post_in_context, post_in_db)

    def test_post_create_form_context(self):
        """На страницу создания поста передается правильный контекст формы"""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_form_context(self):
        """
        На страницу редактирования поста передается
        верный словарь контекста:
        поля формы и параметр is_edit
        """
        post = Post.objects.get(id=1)
        response = (
            self.authorized_client
            .get(reverse('posts:post_edit', kwargs={'post_id': post.id}))
        )
        context_is_edit = response.context['is_edit']
        self.assertTrue(context_is_edit)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_pages_show_correct_pagination(self):
        """Паджинация страниц работает правильно."""
        page_pagination = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username}),
        ]
        for page in page_pagination:
            response = self.authorized_client.get(page)
            self.assertEqual(
                len(response.context['page_obj']),
                POSTS_PER_PAGE
            )
            response = self.authorized_client.get(page + '?page=2')
            self.assertEqual(
                len(response.context['page_obj']),
                (TEST_POSTS_COUNT - POSTS_PER_PAGE)
            )

    def test_post_appears_correctly(self):
        """
        Пост с группой появляется на главной,
        странице группы и профайле автора, при этом пост
        не появляется на странице другой группы
        """
        post_group = Post.objects.order_by('-pub_date').first()
        pages_for_post = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username}),
        ]
        for page in pages_for_post:
            response = self.authorized_client.get(page)
            group_context = response.context['page_obj'].object_list
            self.assertIn(post_group, group_context)
        response_another_group = (
            self.authorized_client.
            get(reverse(
                'posts:group_list', kwargs={'slug': self.another_group.slug}
            ))
        )
        another_group_context = (
            response_another_group.context['page_obj'].object_list
        )
        self.assertNotIn(post_group, another_group_context)
