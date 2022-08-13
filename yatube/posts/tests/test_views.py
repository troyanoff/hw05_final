import shutil
import tempfile

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

from http import HTTPStatus

from posts.models import Comment, Post, Group, User
from posts.constants import COUNT_POSTS_INDEX
from posts.forms import CommentForm, PostForm
from ..models import Follow


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewsTest(TestCase):
    """Проверка views."""

    @classmethod
    def setUpClass(cls):
        """Создаем тестовые экземпляры User, Post, Group."""
        super().setUpClass()

        cls.user = User.objects.create(
            username='test-username'
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание'
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст 1',
            author=cls.user,
            group=cls.group,
            image=uploaded
        )
        cls.comment = Comment.objects.create(
            text='Тестовый комментарий',
            author=cls.user,
            post=cls.post
        )
        cls.viewer = User.objects.create(username='viewer')
        cls.follow = Follow.objects.create(
            user=cls.viewer,
            author=PostViewsTest.user
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        """Создаем авторизованного клиента и логиним его."""
        self.authorized_user = Client()
        self.authorized_user.force_login(PostViewsTest.user)
        cache.clear()

    def _post_control(self, context):
        """Проверка поста на соответствие PostViewsTest.post."""
        if 'post' in context:
            post = context['post']
        else:
            post = context['page_obj'][0]
        self.assertEqual(post.id, PostViewsTest.post.id)
        self.assertEqual(post.text, PostViewsTest.post.text)
        self.assertEqual(post.author, PostViewsTest.post.author)
        self.assertEqual(post.group, PostViewsTest.post.group)
        self.assertEqual(post.image, PostViewsTest.post.image)

    def test_pages_uses_correct_template(self):
        """URL-адресы используют корректные шаблоны."""
        page_names_templates = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse(
                'posts:group_list',
                kwargs={'slug': PostViewsTest.group.slug}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': PostViewsTest.user.username}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostViewsTest.post.id}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id': PostViewsTest.post.id}
            ): 'posts/create_post.html',
        }

        for reverse_name, template in page_names_templates.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_user.get(reverse_name)
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_paginator_work_correct(self):
        """На страницах работает paginator."""
        self.viewer_client = Client()
        self.viewer_client.force_login(PostViewsTest.viewer)
        for post_number in range(2, 16):
            Post.objects.create(
                text=f'Тестовый текст {post_number}',
                author=PostViewsTest.user,
                group=PostViewsTest.group
            )
        page_posts = {
            '1': COUNT_POSTS_INDEX,
            '2': 5,
        }
        path_list = (
            reverse('posts:index'),
            reverse('posts:follow_index'),
            reverse(
                'posts:group_list',
                kwargs={'slug': PostViewsTest.group.slug}
            ),
            reverse(
                'posts:profile',
                kwargs={'username': PostViewsTest.user.username}
            ),
        )

        for page, posts_count in page_posts.items():
            for path in path_list:
                with self.subTest(path=path):
                    response = self.viewer_client.get(
                        path, {'page': page}
                    )
                    self.assertEqual(
                        len(response.context['page_obj']), posts_count
                    )

    def test_start_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_user.get(reverse('posts:index'))
        self._post_control(response.context)

    def test_follow_page(self):
        """Шаблон follow сформирован с правильным контекстом."""
        self.viewer_client = Client()
        self.viewer_client.force_login(PostViewsTest.viewer)
        response = self.viewer_client.get(reverse('posts:follow_index'))
        self._post_control(response.context)
        Follow.objects.filter(
            user=PostViewsTest.viewer,
            author=PostViewsTest.user
        ).delete()
        response = self.viewer_client.get(reverse('posts:follow_index'))
        self.assertNotIn(
            PostViewsTest.post,
            response.context['page_obj']
        )

    def test_group_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_user.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': PostViewsTest.group.slug}
            )
        )
        self.assertIn('page_obj', response.context)
        self.assertIn('group', response.context)

        self._post_control(response.context)

        group = response.context['group']
        self.assertIsInstance(group, Group)
        self.assertEqual(group, PostViewsTest.group)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_user.get(
            reverse(
                'posts:profile',
                kwargs={'username': PostViewsTest.user.username}
            )
        )
        self.assertIn('page_obj', response.context)
        self.assertIn('author', response.context)
        self.assertIn('posts_count', response.context)
        self.assertIn('following', response.context)

        self._post_control(response.context)

        author = response.context['author']
        self.assertIsInstance(author, User)
        self.assertEqual(author, PostViewsTest.user)

        posts_count = response.context['posts_count']
        self.assertEqual(
            posts_count,
            Post.objects.filter(author=PostViewsTest.user).count()
        )

        self.viewer_client = Client()
        self.viewer_client.force_login(PostViewsTest.viewer)
        response = self.viewer_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': PostViewsTest.user.username}
            )
        )
        following = response.context['following']
        self.assertEqual(
            following,
            Follow.objects.filter(
                user=PostViewsTest.viewer,
                author=PostViewsTest.user
            ).exists()
        )

    def test_post_detail_show_one_post_with_id(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_user.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostViewsTest.post.id}
            )
        )
        self.assertIn('posts_count', response.context)
        self.assertIn('post', response.context)
        self.assertIn('author_post', response.context)
        self.assertIn('post_comments', response.context)
        self.assertIn('form', response.context)

        self._post_control(response.context)
        post = response.context['post']

        posts_count = response.context['posts_count']
        self.assertEqual(posts_count, post.author.posts.count())

        author = response.context['author_post']
        self.assertEqual(author, post.author)
        self.assertIsInstance(author, User)

        last_comment = response.context['post_comments'][0]
        self.assertEqual(
            last_comment,
            PostViewsTest.comment
        )

        form = response.context.get('form')
        self.assertIsInstance(form, CommentForm)

    def test_create_post_form_contains_correct_field(self):
        """Форма создания поста содержит нужные поля."""
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        response = self.authorized_user.get(reverse('posts:post_create'))
        form = response.context.get('form')
        self.assertIsInstance(form, PostForm)

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = form.fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_edit_post_contains_correct_values(self):
        """Форма редактирования поста содержит корректные данные."""
        response = self.authorized_user.get(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': PostViewsTest.post.id}
            )
        )
        self.assertIn('form', response.context)
        self.assertIn('post_id', response.context)
        self.assertIn('is_edit', response.context)

        form = response.context.get('form')
        self.assertIsInstance(form, PostForm)
        self.assertEqual(form.initial['text'], PostViewsTest.post.text)
        self.assertEqual(form.initial['group'], PostViewsTest.group.id)
        self.assertEqual(form.initial['image'], PostViewsTest.post.image)

        post_id = response.context['post_id']
        self.assertEqual(post_id, PostViewsTest.post.id)

        is_edit = response.context['is_edit']
        self.assertTrue(is_edit)

    def test_correct_display_posts(self):
        """Пост не отображается на странице группы, которой не принадлежит."""
        other_user = User.objects.create(
            username='other-username'
        )
        other_group = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-slug-2',
            description='Тестовое описание 2'
        )
        other_post = Post.objects.create(
            text='Другой тестовый текст',
            author=other_user,
            group=other_group
        )
        reverse_kwargs = {
            'posts:group_list': {'slug': PostViewsTest.group.slug},
            'posts:profile': {'username': PostViewsTest.user.username}
        }
        for reverse_path, kwargs in reverse_kwargs.items():
            with self.subTest(reverse_path=reverse_kwargs):
                response = self.authorized_user.get(
                    reverse(reverse_path, kwargs=kwargs)
                )
                first_post = response.context['page_obj'][0]
                self.assertNotEqual(first_post, other_post)

    def test_cache_index(self):
        """На главной странице работает кэширование."""
        response = self.authorized_user.get(reverse('posts:index'))
        cache_1 = response.content
        Post.objects.create(
            text='Я не попал в кэш.',
            author=PostViewsTest.user
        )
        response = self.authorized_user.get(reverse('posts:index'))
        cache_2 = response.content
        self.assertEqual(cache_1, cache_2)

    def test_follow_unfollow(self):
        self.authorized_user.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': PostViewsTest.viewer.username}
            )
        )
        self.assertTrue(
            Follow.objects.filter(
                user=PostViewsTest.user,
                author=PostViewsTest.viewer
            ).exists()
        )
        self.authorized_user.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': PostViewsTest.viewer.username}
            )
        )
        self.assertFalse(
            Follow.objects.filter(
                user=PostViewsTest.user,
                author=PostViewsTest.viewer
            ).exists()
        )
