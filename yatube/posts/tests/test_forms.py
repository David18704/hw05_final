from django.test import TestCase, Client
from django.urls import reverse
from django.conf import settings

from posts.models import Post, Group, User
from posts.forms import PostForm

import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

        cls.reader_user = User.objects.create_user(username='admin1')
        cls.writer_user = User.objects.create_user(username='admin2')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_group',
            description='Тестирование'
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
            content_type='image/gif')
        cls.form = PostForm()
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=PostCreateFormTests.writer_user,
            group=PostCreateFormTests.group,
            image=uploaded,
            )
    
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()
    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostCreateFormTests.writer_user)
    
    def test_image_index(self):
        response = self.authorized_client.get(
            reverse('index'))
        #postq = response.context['page'].object_list[0]
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст',
                group=PostCreateFormTests.group.id,
                author=PostCreateFormTests.writer_user,
                image='posts/small.gif'
            ).exists()
        )
    def test_image_profile(self):
        response = self.authorized_client.get(
           reverse('profile', kwargs={'username': 'admin2'}))
        #postq = response.context['page'].object_list[0]
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст',
                group=PostCreateFormTests.group.id,
                author=PostCreateFormTests.writer_user,
                image= 'posts/small.gif'
            ).exists()
        )
    def test_image_group_posts(self):
        response = self.authorized_client.get(
        reverse('group_posts', kwargs={'slug': 'test_group'}))
        #postq = response.context['page'].object_list[0]
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст',
                group=PostCreateFormTests.group.id,
                author=PostCreateFormTests.writer_user,
                image= 'posts/small.gif'
            ).exists()
        )
    def test_image_post(self):
        response = self.authorized_client.get(
            reverse('post', kwargs={'username': 'admin2', 'post_id': '1'}))
        #postq = response.context['posts'][0]
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст',
                group=PostCreateFormTests.group.id,
                author=PostCreateFormTests.writer_user,
                image= 'posts/small.gif'
            ).exists()
        )
        
    def test_image_new_post(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст',
            'group': PostCreateFormTests.group.id,
            'image': 'posts/small.gif',
        }
        response = self.authorized_client.post(
            reverse('new_post'),
            data=form_data,
            
            follow=True
        )
        self.assertRedirects(response, reverse('index'))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст',
                group=PostCreateFormTests.group.id,
                author=PostCreateFormTests.writer_user,
                image= 'posts/small.gif'
            ).exists()
        )

    def test_create_post(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст',
            'group': PostCreateFormTests.group.id
        }
        response = self.authorized_client.post(
            reverse('new_post'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('index'))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст',
                group=PostCreateFormTests.group.id,
                author=PostCreateFormTests.writer_user
            ).exists()
        )

    def test_create_post_without_group(self):
        posts_count_new = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст2',
            'group': ''
        }
        response = self.authorized_client.post(
            reverse('new_post'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('index'))
        self.assertEqual(Post.objects.count(), posts_count_new + 1)
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст2',
                author=PostCreateFormTests.writer_user
            ).exists()
        )

    def test_username_post_edit_save(self):
        form_data = {
            'text': 'Измененный текст',
            'group': PostCreateFormTests.group.id
        }
        response = self.authorized_client.post(
            reverse('post_edit', kwargs={'username': 'admin2', 'post_id': 1}),
            data=form_data,
            follow=True
        )

        self.assertRedirects(response,
            reverse('post', kwargs={'username': 'admin2','post_id': 1})
            )
        self.assertTrue(
            Post.objects.filter(
                text='Измененный текст',
                group=PostCreateFormTests.group.id,
                author=PostCreateFormTests.writer_user,
            ).exists()
        )

    def test_another_post_edit_save(self):
        form_data = {
            'text': 'Вторично измененный текст',
            'group': ''
        }
        response = self.authorized_client.post(
            reverse('post_edit', kwargs={'username': 'admin2', 'post_id': 1}),
            data=form_data,
            follow=True
        )

        self.assertRedirects(response, 
            reverse('post', kwargs={'username': 'admin2','post_id': 1})
            )
        self.assertTrue(
            Post.objects.filter(
                text='Вторично измененный текст',
                author=PostCreateFormTests.writer_user,
                group__isnull=True
            ).exists()
        )




