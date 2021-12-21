from django.test import Client, TestCase
from django.urls import reverse

from ..forms import PostForm
from ..models import Group, Post, User


USERNAME = 'test-username'
POST_CREATE = 'posts:post_create'


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.group = Group.objects.create(
            title='Текстовый заголовок',
            slug='test-slug',
            description='Текстовое описание'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            group=cls.group,
            text='Текстовый текст'
        )
        cls.form = PostForm()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

        cls.PROFILE = 'posts:profile'
        cls.POST_DETAIL = 'posts:post_detail'
        cls.POST_EDIT = 'posts:post_edit'

    def test_create_post(self):
        posts_num = Post.objects.count()
        form_data = {
            'text': 'Текстовый текст',
            'group': self.group.id,
        }
        response = self.authorized_client.post(
            reverse(POST_CREATE),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(self.PROFILE,
                                               kwargs={'username': USERNAME}))
        self.assertEqual(Post.objects.count(), posts_num + 1)
        last_post = Post.objects.latest('id')
        self.assertEqual(last_post.text, form_data['text'])
        self.assertEqual(last_post.group.id, form_data['group'])

    def test_post_edit(self):
        form_data = {
            'text': 'Новый пост',
            'group': self.group.pk,
        }
        posts_count = Post.objects.count()
        response = self.authorized_client.post(
            reverse(self.POST_EDIT, kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True
        )
        post_response = response.context['post']
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(post_response.text, form_data['text'])
        self.assertEqual(post_response.author, self.user)
        self.assertEqual(post_response.group.pk, form_data['group'])
        self.assertRedirects(response,
                             reverse(self.POST_DETAIL,
                                     kwargs={'post_id': self.post.pk}))

    def test_anonymous_create_post(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Текстовый текст',
            'group': self.group.id,
        }
        response = self.client.post(
            reverse(POST_CREATE),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertRedirects(response, (reverse('users:login') + '?next='
                                        + reverse(POST_CREATE)))

    def test_anonymous_edit_post(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Текст',
            'group': 'other',
        }
        response = self.client.post(
            reverse(self.POST_EDIT, kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertRedirects(response, (reverse('users:login')) + '?next='
                             + (reverse(self.POST_EDIT,
                                        kwargs={'post_id': self.post.pk})))
        post = Post.objects.get(id=self.post.id)
        self.assertNotEqual(post.text, form_data['text'])
        self.assertNotEqual(post.group.id, form_data['group'])
