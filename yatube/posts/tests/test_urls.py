from django.test import TestCase, Client
from django.urls import reverse

from http import HTTPStatus

from posts.models import Post, Group, User


class PostsURLTests(TestCase):
    """Проверка URL."""

    @classmethod
    def setUpClass(cls):
        """Создаем тестовые поля моделей Post, Group и User."""
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_username')
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание'
        )

    def setUp(self):
        """Создаем неавторизованного клиента и логиним авторизованного."""
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostsURLTests.user)

    def test_urls_uses_correct_template(self):
        """"URL-адреса используют ожидаемые шаблоны."""
        urls_template = {
            '/': 'posts/index.html',
            '/follow/': 'posts/follow.html',
            f'/group/{PostsURLTests.group.slug}/': 'posts/group_list.html',
            f'/profile/{PostsURLTests.user.username}/': 'posts/profile.html',
            f'/posts/{PostsURLTests.post.id}/': 'posts/post_detail.html',
            f'/posts/{PostsURLTests.post.id}/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }

        for address, template in urls_template.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_redirect_viewers(self):
        """Проверка перенаправления на другие URL
           не имеющих прав доступа пользователей.
        """
        self.viewer = User.objects.create(username='viewer')
        self.viewer_client = Client()
        self.viewer_client.force_login(self.viewer)

        post_id = PostsURLTests.post.id
        urls_redirect = {
            f'/posts/{post_id}/edit/': f'/posts/{post_id}/',
        }

        for url, next_url in urls_redirect.items():
            with self.subTest(url=url):
                response = self.viewer_client.get(url, follow=True)
                self.assertRedirects(response, next_url)

        self.authorized_client.force_login(PostsURLTests.user)

    def test_urls_redirect_anonymous(self):
        """Проверка перенаправления на другие URL
           анонимных пользователей.
        """

        urls_redirect = {
            '/create/': reverse('auth:login'),
            f'/posts/{PostsURLTests.post.id}/edit/': reverse('auth:login'),
        }

        for url, next_url in urls_redirect.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url, follow=True)
                self.assertRedirects(response, f'{next_url}?next={url}')

    def test_urls_error_non_existent_page(self):
        """Проверка несуществующего URL-адреса на ошибку."""
        response = self.authorized_client.get('/i_do_not_exist/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND.value)
        self.assertTemplateUsed(response, 'core/404.html')
