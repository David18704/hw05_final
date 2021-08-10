from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.conf import settings
from django import forms
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.models import Post, Group, User, Follow, Comment

import shutil


class GroupviewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(
            first_name='David',
            last_name='Elchaninov',
            username='admin1')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test')
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=GroupviewsTests.user,
            group=GroupviewsTests.group)

    def setUp(self):
        self.user = User.objects.create_user(username='Petruchchio')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_pages_use_correct_template(self):
        templates_pages_names = {
            'posts/index.html': reverse('index'),
            'posts/new_post.html': reverse('new_post'),
            'posts/group.html': (
                reverse('group_posts', kwargs={'slug': 'test'})
            ),
        }
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(
            first_name='David',
            last_name='Elchaninov',
            username='admin1')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test')

        Post.objects.bulk_create((Post(text='Текст', author=cls.user)
                                  for _ in range(13)))

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_first_page_contains_ten_records(self):
        response = self.authorized_client.get(reverse('index'))
        self.assertEqual(len(response.context['page'].object_list), 10)

    def test_second_page_contains_three_records(self):
        response = self.authorized_client.get(reverse('index') + '?page=2')
        self.assertEqual(len(response.context['page'].object_list), 3)


class GrouppagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(
            first_name='David',
            last_name='Elchaninov',
            username='admin1')
        cls.group = Group.objects.create(
            title='Тест',
            slug='Test',
            description='Test')
        cls.another_group = Group.objects.create(
            title='Тест1',
            slug='Test1',
            description='Test1')
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=GrouppagesTests.user,
            group=GrouppagesTests.group)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_newpost_correct_context(self):
        response = self.authorized_client.get(reverse('new_post'))
        form_fields = {

            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,

        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_username_post_edit_correct_context(self):
        response = self.authorized_client.get(
            reverse('post_edit', kwargs={'username': 'admin1',
                                         'post_id': GrouppagesTests.post.id}))
        form_data = {

            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_data.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_home_page_correct_context(self):
        response = self.authorized_client.get(reverse('index'))
        first_object = response.context['page'].object_list[0]

        self.assertEqual(first_object.text, 'Тестовый текст')
        self.assertEqual(first_object.author.username, 'admin1')
        self.assertEqual(first_object.group.title, 'Тест')

    def test_username_correct_context(self):
        response = self.authorized_client.get(
            reverse('profile', kwargs={'username': 'admin1'})
        )
        self.assertEqual(response.context['author'].username, 'admin1')

        post = response.context['page'].object_list[0]

        self.assertEqual(post.text, 'Тестовый текст')
        self.assertEqual(post.group.title, 'Тест')
        self.assertTrue(post.group.title != 'Тест1')

    def test_username_post_correct_context(self):
        response = self.authorized_client.get(
            reverse('post', kwargs={'username': 'admin1',
                    'post_id': GrouppagesTests.post.id}))

        self.assertEqual(response.context['user'].username, 'admin1')
        self.assertEqual(response.context['post_id'], GrouppagesTests.post.id)

        post = response.context['posts'][0]

        self.assertTrue(post)
        self.assertEqual(post.text, 'Тестовый текст')
        self.assertEqual(post.group.title, 'Тест')
        self.assertTrue(post.group.title != 'Тест1')

    def test_group_detail_correct_context(self):
        response = self.authorized_client.get(
            reverse('group_posts', kwargs={'slug': 'Test'})
        )

        self.assertEqual(response.context['group'].title, 'Тест')
        self.assertEqual(response.context['group'].description, 'Test')
        self.assertEqual(response.context['group'].slug, 'Test')
        self.assertEqual(len(response.context['page']), 1)

        response = self.authorized_client.get(
            reverse('group_posts', kwargs={'slug': 'Test1'}))

        self.assertEqual(len(response.context['page']), 0)


class CacheTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(
            first_name='David',
            last_name='Elchaninov',
            username='admin1')
        cls.group = Group.objects.create(
            title='Тест',
            slug='Test',
            description='Test')
        cls.another_group = Group.objects.create(
            title='Тест1',
            slug='Test1',
            description='Test1')
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=CacheTests.user,
            group=CacheTests.group)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_cache_index(self):
        Post.objects.create(text='тест для  кэша', author=CacheTests.user),
        response = self.authorized_client.get(reverse('index'))
        self.assertEqual(len(response.context['page'].object_list), 2)

        first_object = response.context['page'].object_list[0]
        self.assertEqual(first_object.text, 'тест для  кэша')

        CacheTests.post.delete()
        self.assertEqual(len(response.context['page'].object_list), 2)
        cache.clear()

        response = self.authorized_client.get(reverse('index'))
        self.assertEqual(len(response.context['page'].object_list), 1)


class FollowsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(
            first_name='David',
            last_name='Elchaninov',
            username='admin1')
        cls.author = User.objects.create(
            first_name='David',
            last_name='Elchaninov',
            username='admin2')
        cls.non_signatory = User.objects.create(
            first_name='David',
            last_name='Elchaninov',
            username='admin3')
        cls.group = Group.objects.create(
            title='Тест',
            slug='Test',
            description='Test')
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=FollowsTests.user,
            group=FollowsTests.group)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_comment(self):
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'Комментарий',
        }

        self.guest_client.post(reverse('add_comment',
                               kwargs={'username': 'admin1',
                                       'post_id': FollowsTests.post.id}),
                               data=form_data,
                               follow=True)
        self.assertEqual(Comment.objects.count(), comment_count)

        self.authorized_client.post(reverse('add_comment',
                                    kwargs={'username': 'admin1',
                                            'post_id': FollowsTests.post.id}),
                                    data=form_data,
                                    follow=True)
        self.assertEqual(Comment.objects.count(), comment_count + 1)

    def test_follow_author(self):
        follow_count = Follow.objects.count()

        self.authorized_client.get(reverse('profile_follow',
                                   kwargs={'username': 'admin2'}))
        self.assertEqual(Follow.objects.count(), follow_count + 1)

    def test_unfollow_author(self):
        follow_count = Follow.objects.count()

        self.authorized_client.get(reverse('profile_unfollow',
                                   kwargs={'username': 'admin2'}))
        self.assertEqual(Follow.objects.count(), follow_count)

    def test_follow_myself(self):

        self.authorized_client.get(reverse('profile_follow',
                                   kwargs={'username': 'admin1'}))
        self.assertEqual(FollowsTests.user.follower.count(), 0)

    def test_follow_repeat(self):
        follow_count = Follow.objects.count()

        self.authorized_client.get(reverse('profile_follow',
                                   kwargs={'username': 'admin2'}))
        self.assertEqual(Follow.objects.count(), follow_count + 1)

        self.authorized_client.get(reverse('profile_follow',
                                   kwargs={'username': 'admin2'})
                                   )
        self.assertEqual(Follow.objects.count(), follow_count + 1)

    def test_follow_post_non_signatory(self):

        Post.objects.create(text="тест для  подписки",
                            author=FollowsTests.non_signatory),
        response = self.authorized_client.get(reverse('follow_index'))
        self.assertEqual(len(response.context['page'].object_list), 0)

    def test_follow_post_author(self):

        Follow.objects.create(user=FollowsTests.user,
                              author=FollowsTests.author),
        Post.objects.create(text="тест для  подписки",
                            author=FollowsTests.author),
        response = self.authorized_client.get(reverse('follow_index'))
        self.assertEqual(len(response.context['page'].object_list), 1)


@override_settings(MEDIA_ROOT='foo/bar/')
class PostCreateImageTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

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
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=PostCreateImageTests.writer_user,
            group=PostCreateImageTests.group,
            image=uploaded)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostCreateImageTests.writer_user)

    def test_image_index(self):
        self.authorized_client.get(reverse('index'))
        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст',
                group=PostCreateImageTests.group.id,
                author=PostCreateImageTests.writer_user,
                image='posts/small.gif'
            ).exists()
        )

    def test_image_profile(self):
        response = self.authorized_client.get(
            reverse('profile', kwargs={'username': 'admin2'}))

        self.assertEqual(len(response.context['page']), 1)

        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст',
                group=PostCreateImageTests.group.id,
                author=PostCreateImageTests.writer_user,
                image='posts/small.gif'
            ).exists()
        )

    def test_image_groupe(self):
        self.authorized_client.get(
            reverse('group_posts', kwargs={'slug': 'test_group'}))

        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст',
                group=PostCreateImageTests.group.id,
                author=PostCreateImageTests.writer_user,
                image='posts/small.gif'
            ).exists()
        )

    def test_image_post(self):
        self.authorized_client.get(
            reverse('post', kwargs={'username': 'admin2',
                                    'post_id': PostCreateImageTests.post.id}))

        self.assertTrue(
            Post.objects.filter(
                text='Тестовый текст',
                group=PostCreateImageTests.group.id,
                author=PostCreateImageTests.writer_user,
                image='posts/small.gif'
            ).exists()
        )
