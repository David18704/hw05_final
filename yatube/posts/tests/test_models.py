from django.test import TestCase

from posts.models import Post, Group, User


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(
            first_name='David',
            last_name='Elchaninov',
            username='admin1',
        )          
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=PostModelTest.user,
        )

    def test_str_post(self):
        test_str = PostModelTest.post
        expected_object_name = test_str.text[:15]
        self.assertEqual(expected_object_name, str(test_str))


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title="Тест",
            slug="Test",
            description="Test")

    def test_str_post(self):
        test_str1 = GroupModelTest.group
        expected_object_name = test_str1.title
        self.assertEqual(expected_object_name, str(test_str1))
