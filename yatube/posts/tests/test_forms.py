from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from posts.models import Group, Post

User = get_user_model()


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='StasBasov')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание группы'
        )
        cls.post = Post.objects.create(
            text='Тестовая запись в посте',
            author=cls.user,
            group=cls.group
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_guest_create_post(self):
        """Проверка: неавторизованный пользователь
        не может создать запись.
        """
        form_data = {
            'text': 'Тестовый пост',
            'group': self.group.pk,
        }
        self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertFalse(
            Post.objects.filter(
                text=form_data['text']
            ).exists()
        )

    def test_create_post(self):
        """Проверка создания поста и редирект в профиль"""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст',
            'group': self.group.pk,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                group=self.group.pk,
                author=self.user,
                text=form_data['text']
            ).exists()
        )
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.user})
        )

    def test_authorized_edit_post(self):
        """Редактирование записи создателем поста"""
        form_data = {
            'text': 'Измененный текст поста',
            'group': self.group.pk
        }
        response_edit = self.authorized_client.post(
            reverse('posts:post_edit',
                    kwargs={
                        'post_id': self.post.pk
                    }),
            data=form_data,
            follow=True,
        )
        self.assertEqual(response_edit.status_code, HTTPStatus.OK)
        self.assertTrue(
            Post.objects.filter(text=form_data['text'],
                                author=self.user,
                                group=self.group,
                                id=self.post.id
                                ).exists())
