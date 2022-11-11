from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from posts.models import Post, Group

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='HasNoName')
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.adress_post = f'/posts/{cls.post.id}/'
        cls.address_edit = f'/posts/{cls.post.id}/edit/'
        cls.address_slug = f'/group/{cls.group.slug}/'
        cls.address_user = f'/profile/{cls.user.username}/'

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_home_url_exists_at_desired_location(self):
        """Главная страница  доступна любому пользователю."""
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_home_url_exists_at_desired_location_authorized(self):
        """Главная страница доступна авторизованному пользователю."""
        response = self.authorized_client.get('/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_group_detail_url_exists_at_desired_location(self):
        """Страница group/<slug:slug>/ доступна любому пользователю."""
        response = self.guest_client.get(self.address_slug)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_group_detail_url_exists_at_desired_location_authorized(self):
        """Страница group/<slug:slug>/ доступна
        авторизованному пользователю.
        """
        response = self.authorized_client.get(self.address_slug)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_profile_url_exists_at_desired_location(self):
        """Страница profile/<str:username>/ доступна любому пользователю."""
        response = self.guest_client.get(self.address_user)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_profile_url_exists_at_desired_location_authorized(self):
        """Страница profile/<str:username>/ доступна
        авторизованному пользователю.
        """
        response = self.authorized_client.get(self.address_user)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_posts_url_exists_at_desired_location(self):
        """Страница posts/<int:post_id>/ доступна любому пользователю."""
        response = self.guest_client.get(self.adress_post)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_posts_url_exists_at_desired_location_authorized(self):
        """Страница posts/<int:post_id>/ доступна
        авторизованному пользователю.
        """
        response = self.authorized_client.get(self.adress_post)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_posts_edit_url_exists_at_desired_location(self):
        """Страница /edit/ доступна авторизованному пользователю."""
        response = self.authorized_client.get(self.address_edit)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_posts_create_url_exists_at_desired_location(self):
        """Страница /create/ доступна авторизованному пользователю."""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unexisting_page(self):
        """Страница /unexisting_page/ доступна любому пользователю."""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            self.address_slug: 'posts/group_list.html',
            self.address_user: 'posts/profile.html',
            self.adress_post: 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            self.address_edit: 'posts/create_post.html',
            '/': 'posts/index.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_404(self):
        """Проверка кастомного шаблона 404."""
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
