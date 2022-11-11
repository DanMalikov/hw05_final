from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

from posts.models import Post, Group, Comment, Follow
import tempfile

User = get_user_model()


class TaskPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.user = User.objects.create_user(username='StasBasov')
        cls.group = Group.objects.create(
            title='Тестовая Группа',
            slug='test-slug',
            description='Тестовое описание'
        )
        cls.group_2 = Group.objects.create(
            title='Еще одна тестовая Группа',
            slug='test-line',
            description='Еще одно тестовое описание'
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
            group=cls.group,
            image=cls.uploaded
        )
        cls.form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', kwargs={'slug': self.group.slug}):
            'posts/group_list.html',
            reverse('posts:profile', kwargs={'username': self.user.username}):
            'posts/profile.html',
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}):
            'posts/post_detail.html',
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}):
            'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertIn('page_obj', response.context)
        image_in_post = Post.objects.first().image
        self.assertEqual(image_in_post, 'posts/small.gif')

    def test_group_list_pages_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:group_list',
            kwargs={'slug': self.group.slug})
        )
        self.assertIn('group', response.context)
        self.assertEqual(response.context['group'], self.group)
        self.assertIn('page_obj', response.context)
        image_in_post = Post.objects.first().image
        self.assertEqual(image_in_post, 'posts/small.gif')

    def test_post_profile_pages_show_correct_contexte(self):
        """Шаблон post_profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': 'StasBasov'}
            )
        )
        self.assertIn('page_obj', response.context)
        self.assertEqual(response.context['author'], self.user)
        image_in_post = Post.objects.first().image
        self.assertEqual(image_in_post, 'posts/small.gif')

    def test_post_detail_pages_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.pk})
        )
        self.assertEqual(response.context.get('post'), self.post)
        image_in_post = Post.objects.first().image
        self.assertEqual(image_in_post, 'posts/small.gif')

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = (self.authorized_client.get(reverse(
            'posts:post_edit', kwargs={'post_id': self.post.pk}))
        )
        for value, expected in self.form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
                self.assertEqual(response.context['is_edit'], True)

    def test_create_post_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:post_create')
        )
        for value, expected in self.form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_show_post_correct_on_pages(self):
        """Проверка: пост появится на главной, на странице группы
        и в профайле пользователя.
        """
        pages_names = (
            reverse('posts:index'),
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}
            ),
            reverse(
                'posts:profile',
                kwargs={'username': self.user.username}
            ),
        )

        for name_page in pages_names:
            with self.subTest(name_page=name_page):
                response = self.authorized_client.get(name_page)
                post = response.context['page_obj'][0]
                self.assertEqual(post.author, self.post.author)
                self.assertEqual(post.text, self.post.text)
                self.assertEqual(post.group.title, self.post.group.title)

    def test_no_post_in_another_group_page(self):
        """Проверка: пост не попал в другую группу"""
        response = self.guest_client.get(reverse(
            'posts:group_list',
            kwargs={'slug': self.group_2.slug}))
        posts = response.context['page_obj']
        self.assertEqual(0, len(posts))

    def test_post_detail_page_comment_for_guest_user(self):
        '''Комментирование неавторизованным пользователем'''
        form_data = {
            'text': 'text'
        }
        response_member = self.guest_client.get(
            reverse('posts:add_comment', kwargs={
                'post_id': self.post.pk}
            ),
            data=form_data,
            follow=True
        )
        self.assertEqual(response_member.status_code, HTTPStatus.OK.value)

    def test_comment(self):
        """Проверка: Комментарий появляется на странице поста."""
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'Новый комментарий',
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertTrue(
            Comment.objects.filter(text=form_data['text']).exists()
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.pk}))

    def test_cache_index(self):
        """Кеширование главной страницы."""
        first_try = self.authorized_client.get(reverse('posts:index'))
        post = Post.objects.get(pk=1)
        post.text = 'Текст'
        post.save()
        second_try = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(first_try.content, second_try.content)
        cache.clear()
        third_try = self.authorized_client.get(reverse('posts:index'))
        self.assertNotEqual(first_try.content, third_try.content)


class FollowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_follower = User.objects.create_user(username='user')
        cls.user_follower_2 = User.objects.create_user(username='user_1')
        cls.post = Post.objects.create(
            author=cls.user_follower_2,
            text='Тестовый текст',
        )

    def setUp(self):
        self.follow_client = Client()
        self.follower_client = Client()
        self.follow_client.force_login(self.user_follower_2)
        self.follower_client.force_login(self.user_follower)

    def test_follow(self):
        """Зарегистрированный может подписываться."""
        follower_count = Follow.objects.count()
        self.follower_client.get(reverse(
            'posts:profile_follow',
            args=(self.user_follower_2.username,)))
        self.assertEqual(Follow.objects.count(), follower_count + 1)

    def test_unfollow(self):
        """Зарегистрированный может отписываться."""
        Follow.objects.create(
            user=self.user_follower,
            author=self.user_follower_2
        )
        follower_count = Follow.objects.count()
        self.follower_client.get(reverse(
            'posts:profile_unfollow',
            args=(self.user_follower_2.username,)))
        self.assertEqual(Follow.objects.count(), follower_count - 1)

    def test_new_post_see_follower(self):
        """Пост появляется в ленте подписанных пользователей."""
        posts = Post.objects.create(
            text=self.post.text,
            author=self.user_follower_2,
        )
        follow = Follow.objects.create(
            user=self.user_follower,
            author=self.user_follower_2
        )
        response = self.follower_client.get(reverse('posts:follow_index'))
        post = response.context['page_obj'][0]
        self.assertEqual(post, posts)
        follow.delete()
        response_2 = self.follower_client.get(reverse('posts:follow_index'))
        self.assertEqual(len(response_2.context['page_obj']), 0)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='BasovStas')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание'
        )
        cls.first_page_posts = settings.AMOUNT_POSTS
        cls.second_page_posts = cls.first_page_posts // 2
        cls.amount_all_posts = cls.first_page_posts + cls.second_page_posts
        cls.posts = [
            Post(
                author=cls.user,
                text=f'Тестовый пост {number}',
                group=cls.group
            ) for number in range(cls.amount_all_posts)
        ]
        Post.objects.bulk_create(cls.posts)

    def test_first_page_contains_ten_records(self):
        """Проверка постов на первой странице."""
        check_pages = (
            reverse('posts:index'),
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}
            ),
            reverse(
                'posts:profile',
                args=[self.user]
            ),
        )
        for value in check_pages:
            with self.subTest(value=value):
                response = self.client.get(value)
                self.assertEqual(
                    len(response.context['page_obj']),
                    self.first_page_posts
                )

    def test_second_page_contains_three_records(self):
        """Проверка постов на второй странице."""
        check_pages = (
            reverse(
                'posts:index'
            ),
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}
            ),
            reverse(
                'posts:profile',
                args=[self.user]
            ),
        )
        for value in check_pages:
            with self.subTest(value=value):
                response = self.client.get(value + '?page=2')
                self.assertEqual(
                    len(response.context['page_obj']),
                    self.second_page_posts
                )
