import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.models import Comment, Post, Group

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormsTest(TestCase):
    """Проверка forms."""

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
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group
        )

    @classmethod
    def tearDownClass(cls):
        """После выполнения тестов, удаляем временную папку."""
        super().tearDownClass()

        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        """Создаем авторизованного клиента и логиним его."""
        self.authorized_user = Client()
        self.authorized_user.force_login(PostFormsTest.user)

    def test_create_post_successfully(self):
        """Создание поста проходит успешно."""
        count_post = Post.objects.count()
        changed_text = 'Тестовый текст 2'
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
        form = {
            'text': changed_text,
            'group': PostFormsTest.group.id,
            'image': uploaded,
        }
        response = self.authorized_user.post(
            reverse('posts:post_create'),
            form
        )
        redirect_path = reverse(
            'posts:profile',
            kwargs={'username': PostFormsTest.user.username}
        )
        self.assertTrue(
            Post.objects.filter(
                text=changed_text,
                group=PostFormsTest.group,
                image='posts/small.gif'
            ).exists()
        )
        self.assertRedirects(response, redirect_path)
        self.assertEqual(Post.objects.count(), count_post + 1)

    def test_create_post_anonymous_author(self):
        """Анонимный пользователь не может создать пост."""
        self.anon_user = Client()
        count_post = Post.objects.count()

        form = {
            'text': 'Запись анонимного пользователя',
            'group': PostFormsTest.group.id,
        }
        response = self.anon_user.post(
            reverse('posts:post_create'),
            form, follow=True
        )
        self.assertRedirects(
            response,
            '{redirect}?next={next_url}'.format(
                redirect=reverse('users:login'),
                next_url=reverse('posts:post_create')
            )
        )
        self.assertEqual(Post.objects.count(), count_post)
        self.assertFalse(
            Post.objects.filter(
                text='Запись анонимного пользователя'
            ).exists()
        )

    def test_edit_post_text_editing_successfully(self):
        """Редактирование текста поста проходит успешно."""
        form = {'text': 'Измененный тестовый текст'}
        self.authorized_user.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': PostFormsTest.post.id}
            ),
            form
        )
        PostFormsTest.post.refresh_from_db()
        self.assertEqual(PostFormsTest.post.text, 'Измененный тестовый текст')

    def test_edit_post_group_editing_successfully(self):
        """Изменение группы у поста проходит успешно.
        Пост отображается в нужной группе.
        Пост больше не отображается в старой группе."""
        group = Group.objects.create(
            title='Другая группа',
            slug='other-group',
            description='Другое описание'
        )
        form = {
            'text': PostFormsTest.post.text,
            'group': group.id
        }
        self.authorized_user.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': PostFormsTest.post.id}
            ),
            form
        )
        PostFormsTest.post.refresh_from_db()
        self.assertEqual(PostFormsTest.post.group, group)

        response = self.authorized_user.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': group.slug}
            )
        )
        last_post_group = response.context['page_obj'][0]
        self.assertEqual(last_post_group, PostFormsTest.post)

        response = self.authorized_user.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': PostFormsTest.group.slug}
            )
        )
        posts_old_group = response.context['page_obj']
        self.assertNotIn(PostFormsTest.post, posts_old_group)

    def test_add_comment_successfully(self):
        """Добавление комментария проходит успешно."""
        comment = 'Новый комментарий'
        form = {
            'text': comment,
        }
        self.authorized_user.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': PostFormsTest.post.id}
            ),
            form
        )
        Comment.objects.get(id=1).refresh_from_db()
        self.assertTrue(Comment.objects.filter(
            text=comment).exists()
        )

    def test_add_comment_anonymous_author(self):
        """Анонимный пользователь не может добавить комментарий."""
        self.anon_user = Client()
        count_comment = Comment.objects.count()

        comment = 'Комментарий анонимного пользователя'
        form = {
            'text': comment,
        }
        response = self.anon_user.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': PostFormsTest.post.id}
            ),
            form, follow=True
        )
        self.assertRedirects(
            response,
            '{redirect}?next={next_url}'.format(
                redirect=reverse('users:login'),
                next_url=reverse(
                    'posts:add_comment',
                    kwargs={'post_id': PostFormsTest.post.id}
                )
            )
        )
        self.assertEqual(Comment.objects.count(), count_comment)
        self.assertFalse(
            Comment.objects.filter(
                text=comment
            ).exists()
        )
