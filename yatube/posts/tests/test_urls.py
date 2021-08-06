from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django.urls import reverse
from django.core.cache import cache

from posts.models import Post, Group, User, Follow, Comment

from http import HTTPStatus

User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.user = User.objects.create(
            first_name='David',
            last_name='Elchaninov',
            username='admin1')
        cls.user2 = User.objects.create(
            first_name='David',
            last_name='Elchaninov',
            username='admin2')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            slug='test')
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=StaticURLTests.user,
            pub_date='14.07.2021',
            group=StaticURLTests.group)
        cls.post2 = Post.objects.create(
            text='Тестовый текст',
            author=StaticURLTests.user2,
            pub_date='14.07.2021',
            group=StaticURLTests.group)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_homepage(self):
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_newpage(self):
        response = self.authorized_client.get(reverse('new_post'))
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_group(self):
        response = self.authorized_client.get(
            reverse('group_posts', kwargs={'slug': 'test'})
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_profile(self):
        response = self.authorized_client.get(
            reverse('profile', kwargs={'username': 'admin1'})
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post(self):
        response = self.authorized_client.get(
            reverse('post', kwargs={'username': 'admin1', 'post_id': '1'})
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit(self):
        response = self.authorized_client.get(
            reverse('post_edit', kwargs={'username': 'admin1', 'post_id': '1'})
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        response = self.authorized_client.get(
            reverse('post_edit', kwargs={'username': 'admin2', 'post_id': '2'})
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        response = self.guest_client.get(
            reverse('post_edit', kwargs={'username': 'admin1', 'post_id': '1'})
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_urls_uses_correct_template(self):
        templates_url_names = {
            'posts/index.html': '',
            'posts/new_post.html': '/new/',
            'posts/group.html': '/group/test/',
        }
        for template, adress in templates_url_names.items():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertTemplateUsed(response, template)

    def test_about_url_edit_correct_template(self):
        response = self.authorized_client.get('/admin1/1/edit/')
        self.assertTemplateUsed(response, 'posts/new_post.html')

    def test_post_edit_redirect(self):
        response = self.guest_client.get('/admin1/1/edit/', follow=True)
        self.assertRedirects(
            response, '/auth/login/?next=/admin1/1/edit/')

        response = self.authorized_client.get('/admin2/2/edit/', follow=True)
        self.assertRedirects(
            response, '/admin2/2/')

    def test_url_not_found(self):
        response = self.guest_client.get('/404/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)


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

    def test_signatore(self):
        follow_count = Follow.objects.count()
        response = self.authorized_client.get(reverse('profile_follow', 
                                              kwargs={'username': 'admin2'})) 
        self.assertEqual(Follow.objects.count(), follow_count + 1)

        response = self.authorized_client.get(reverse('profile_unfollow',
                                              kwargs={'username': 'admin2'})) 
        self.assertEqual(Follow.objects.count(), follow_count)

    def test_comment(self):
        comment_count = Comment.objects.count()
        form_data = {
            'text': 'Комментарий',
        }

        response = self.guest_client.post(reverse('add_comment', 
                                          kwargs={'username': 'admin1', 'post_id': 1}),
                                          data=form_data,
                                          follow=True)
        self.assertEqual(Comment.objects.count(), comment_count)

        response = self.authorized_client.post(reverse('add_comment', 
                                               kwargs={'username': 'admin1', 
                                                       'post_id': 1}),
                                               data=form_data,
                                               follow=True)
        self.assertEqual(Comment.objects.count(), comment_count + 1)

    def test_follow(self):
        follow_count = Follow.objects.count()

        response = self.authorized_client.get(reverse('profile_follow',
                                              kwargs={'username': 'admin1'}))
        self.assertEqual(Follow.objects.count(), follow_count)

        response = self.authorized_client.get(reverse('profile_follow',
                                              kwargs={'username': 'admin2'}))
        self.assertEqual(Follow.objects.count(), follow_count + 1)

        Post.objects.create(text="тест для  подписки",
                            author=FollowsTests.another_again_user),
        response = self.authorized_client.get(reverse('follow_index'))
        self.assertEqual(len(response.context['page'].object_list), 0)

        Post.objects.create(text="тест для  подписки",
                            author=FollowsTests.another_user),
        response = self.authorized_client.get(reverse('follow_index'))
        self.assertEqual(len(response.context['page'].object_list), 1)
