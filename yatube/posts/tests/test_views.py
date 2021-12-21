from django import forms
from django.conf import settings
from django.test import Client, TestCase
from django.urls import reverse
from django.core.cache import cache

from ..models import Group, Post, User

USERNAME = 'test-username'
INDEX = 'posts:index'
GROUP_LIST = 'posts:group_list'
POST_CREATE = 'posts:post_create'


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.group = Group.objects.create(
            title='test-group',
            slug='test-slug',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group
        )
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

        cls.PROFILE = 'posts:profile'
        cls.POST_DETAIL = 'posts:post_detail'
        cls.POST_EDIT = 'posts:post_edit'

    def test_test_reverse_name_correct_html(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse(INDEX): 'posts/index.html',
            reverse(GROUP_LIST, kwargs={'slug': 'test-slug'}): (
                'posts/group_list.html'
            ),
            reverse(self.PROFILE, kwargs={'username': USERNAME}): (
                'posts/profile.html'
            ),
            reverse(self.POST_DETAIL, args=[self.post.id]): (
                'posts/post_detail.html'
            ),
            reverse(POST_CREATE): (
                'posts/create_post.html'
            ),
            reverse(self.POST_EDIT, args=[self.post.id]): (
                'posts/create_post.html'
            )
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_pages_correct_context(self):
        """Корректный общий context."""
        templates_pages_names = {
            reverse(INDEX),
            reverse(GROUP_LIST, kwargs={'slug': self.group.slug}),
            reverse(self.PROFILE, kwargs={'username': self.user.username}),
            reverse(self.POST_DETAIL, args=[self.post.id]),
        }
        for reverse_name in templates_pages_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                if reverse_name == reverse(self.POST_DETAIL,
                                           args=[self.post.id]):
                    first_object = response.context['post']
                else:
                    first_object = response.context.get('page_obj')[0]
                post_author_0 = first_object.author
                post_id_0 = first_object.pk
                post_text_0 = first_object.text
                post_group_0 = first_object.group.slug
                self.assertEqual(post_text_0, self.post.text)
                self.assertEqual(post_id_0, self.post.pk)
                self.assertEqual(post_author_0, self.post.author)
                self.assertEqual(post_group_0, self.group.slug)

    def test_post_edit_correct_context(self):
        """Корректный context у post_edit."""
        response = self.authorized_client.get(reverse(self.POST_EDIT,
                                                      args=[self.post.id]))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_create_post_correct_context(self):
        """Корректный context у post_create."""
        response = self.authorized_client.get(reverse(POST_CREATE))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context["form"].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_in_main_page(self):
        """Новый пост отображается на главной странице
            и на странице группы."""
        url = ((reverse(INDEX)),
               reverse(GROUP_LIST, kwargs={'slug': self.group.slug}),)
        for urls in url:
            with self.subTest(url=url):
                response = self.authorized_client.get(urls)
                self.assertEqual(len(response.context['page_obj']), 1)

    def test_post_in_profile_page(self):
        """Новый пост попал в профиль."""
        response = self.authorized_client.get(reverse(self.PROFILE,
                                                      args=[USERNAME]))
        posts = response.context['posts']
        self.assertIn(self.post, posts)

    def test_post_not_in_your_group(self):
        """Новый пост попал не в свою группу."""
        response = self.authorized_client.get(
            reverse(
                GROUP_LIST,
                kwargs={'slug': self.group.slug},))
        self.assertNotEqual(response.context.get('page_obj'), self.post)

    def test_index_cache(self):
        """Проверка работы кэша."""
        self.client.post(
            reverse('new_post'),
            data={
                'text': 'test index cache',
                'group': self.group.id,
            },
            follow=True
        )
        response = self.authorized_client.get(reverse('index'))
        self.assertNotContains(response, 'test index cache', status_code=200)
        cache.clear()
        response = self.authorized_client.get(reverse('index'))
        self.assertContains(response, 'test index cache', count=1, status_code=200)


class TestPaginator(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.authorized_client = Client()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.PROFILE = 'posts:profile'
        cls.group = Group.objects.create(
            title='test-group',
            slug='test-slug',
        )
        cls.post = (Post(
            author=cls.user,
            group=cls.group,
            text='Тестовый текст') for i in range(1, 14))
        Post.objects.bulk_create(cls.post)

    def test_first_page_paginator(self):
        """Правильная работа паджинатора на первой странице."""
        urls = [
            reverse(INDEX),
            reverse(GROUP_LIST, kwargs={'slug': self.group.slug}),
            reverse(self.PROFILE, args=[USERNAME]),
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(len(response.context['page_obj']),
                                 settings.NUM_OF_POSTS)

    def test_second_page_paginator(self):
        """Правильная работа паджинатора на второй странице."""
        urls = [
            reverse(INDEX) + '?page=2',
            reverse(GROUP_LIST,
                    kwargs={'slug': self.group.slug}) + '?page=2',
            reverse(self.PROFILE, args=[USERNAME]) + '?page=2',
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(len(response.context['page_obj']), 3)
