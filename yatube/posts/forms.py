from django.contrib.auth import get_user_model
from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _

from .models import Post, Comment


User = get_user_model()


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ['text', 'group', 'image']
        labels = {'text': _('Текст'), 'group': _('Группа'),
                                      'image': _('Изображение')}


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
