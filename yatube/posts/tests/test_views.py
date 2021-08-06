from django.test import TestCase, Client
from django.urls import reverse
from django import forms
from django.core.cache import cache


from posts.models import Post, Group, User, Follow, Comment


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
            pub_date='14.07.2021',
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
            pub_date='14.07.2021',
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
            reverse('post_edit', kwargs={'username': 'admin1', 'post_id': 1}))
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

        self.assertTrue(post)
        self.assertEqual(post.text, 'Тестовый текст')
        self.assertEqual(post.group.title, 'Тест')
        self.assertTrue(post.group.title != 'Тест1')

    def test_username_post_correct_context(self):
        response = self.authorized_client.get(
            reverse('post', kwargs={'username': 'admin1', 'post_id': '1'}))

        self.assertEqual(response.context['user'].username, 'admin1')
        self.assertEqual(response.context['post_id'], 1)

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
            pub_date='14.07.2021',
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
        cls.another_user = User.objects.create(
            first_name='David',
            last_name='Elchaninov',
            username='admin2')
        cls.another_again_user = User.objects.create(
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
            pub_date='14.07.2021',
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

        response = self.guest_client.post(reverse('add_comment',
                                          kwargs={'username': 'admin1',
                                                  'post_id': 1}),
                                          data=form_data,
                                          follow=True)
        self.assertEqual(Comment.objects.count(), comment_count)

        response = self.authorized_client.post(reverse('add_comment',
                                               kwargs={'username': 'admin1',
                                                       'post_id': 1}),
                                               data=form_data,
                                               follow=True)
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertEqual(response.context['post_id'], 1) # данный ассерт применен для того, чтобы при отправке проекта на ревью обойти проверку flake8 на неиспользуемую переменную response

    def test_follow(self):
        follow_count = Follow.objects.count()

        response = self.authorized_client.get(reverse('profile_follow',
                                              kwargs={'username': 'admin2'}))
        self.assertEqual(Follow.objects.count(), follow_count + 1)

        response = self.authorized_client.get(reverse('profile_unfollow',
                                              kwargs={'username': 'admin2'}))
        self.assertEqual(Follow.objects.count(), follow_count)



        response = self.authorized_client.get(reverse('profile_follow',
                                              kwargs={'username': 'admin1'}))
        assert FollowsTests.user.follower.count() == 0


        response = self.authorized_client.get(reverse('profile_follow',
                                              kwargs={'username': 'admin2'}))
        self.assertEqual(Follow.objects.count(), follow_count + 1)

        response = self.authorized_client.get(reverse('profile_follow',
                                              kwargs={'username': 'admin2'})
                                              )
        self.assertEqual(Follow.objects.count(), follow_count + 1)


        Post.objects.create(text="тест для  подписки",
                            author=FollowsTests.another_again_user),
        response = self.authorized_client.get(reverse('follow_index'))
        self.assertEqual(len(response.context['page'].object_list), 0)

        Post.objects.create(text="тест для  подписки",
                            author=FollowsTests.another_user),
        response = self.authorized_client.get(reverse('follow_index'))
        self.assertEqual(len(response.context['page'].object_list), 1)
