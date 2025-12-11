from django.db import models
from django.core.validators import FileExtensionValidator
from django.contrib.auth.models import User
from django.urls import reverse
from mptt.models import MPTTModel, TreeForeignKey
from taggit.managers import TaggableManager
from ckeditor.fields import RichTextField

from apps.services.utils import unique_slugify


class PostManager(models.Manager):
    """
    Кастомный менеджер для модели постов
    """

    def get_queryset(self):
        """
        Список постов (SQL запрос с фильтрацией по статусу опубликованно)
        """
        return super().get_queryset().select_related('author', 'category').filter(status='published')


class Post(models.Model):
    """
    Модель постов
    """
    STATUS_OPTIONS = (
        ('published', 'Опубликовано'),
        ('draft', 'Черновик')
    )
    title = models.CharField(max_length=255, verbose_name='Название поста')
    slug = models.SlugField(max_length=255, blank=True, verbose_name='URL')
    description = RichTextField(config_name='awesome_ckeditor',
                                max_length=500,
                                verbose_name='Краткий текст поста')
    category = TreeForeignKey('Category', on_delete=models.PROTECT,
                              related_name='posts', verbose_name='Категория') 
    text = RichTextField(config_name='awesome_ckeditor',
                         verbose_name='Полный текст поста')
    thumbnail = models.ImageField(
        default='default.jpg',
        blank=True,
        upload_to='images/thumbnails/%Y/%m/%d/',
        verbose_name='Изображение',
        validators=[
            FileExtensionValidator(
                allowed_extensions=('png', 'jpg', 'webp', 'jpeg', 'gif')
            )
        ]
    )
    status = models.CharField(choices=STATUS_OPTIONS, default='published',
                              verbose_name='Статус записи', max_length=10)
    create = models.DateTimeField(auto_now_add=True,
                                  verbose_name='Время добавления')
    update = models.DateTimeField(auto_now=True, verbose_name='Время обновления')
    author = models.ForeignKey(User, on_delete=models.SET_DEFAULT, default=1,
                               related_name='author_posts', verbose_name='Автор')
    updater = models.ForeignKey(User, on_delete=models.SET_NULL,
                                null=True, blank=True,
                                verbose_name='Обновил',
                                related_name='updater_posts')
    fixed = models.BooleanField(verbose_name='Прикреплено', default=False)

    objects = models.Manager()
    custom = PostManager()
    tags = TaggableManager()

    class Meta:
        db_table = 'blog_post'
        ordering = ['-fixed', '-create']
        indexes = [models.Index(fields=['-fixed', '-create', 'status'])]
        verbose_name = 'Статья'
        verbose_name_plural = 'Статьи'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        """
        Получаем прямую ссылку на статью
        """
        return reverse('post_detail', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        """
        При сохранении генерируем слаг и проверяем на уникальность
        """
        self.slug = unique_slugify(self, self.title, self.slug)
        super().save(*args, **kwargs)

    def get_sum_rating(self):
        return sum([rating.value for rating in self.ratings.all()])


class Category(MPTTModel):
    """
    Модель категорий с вложенностью
    """
    title = models.CharField(max_length=255,
                             verbose_name='Название категории')
    slug = models.SlugField(max_length=255, 
                            verbose_name='URL категории', blank=True)
    description = models.TextField(max_length=300,
                                   verbose_name='Описание категории')
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True,
                            blank=True, db_index=True, related_name='children',
                            verbose_name='Родительская категория')

    class MPTTMeta:
        """
        Сортировка по вложенности
        """
        order_insertion_by = ('title',)

    class Meta:
        """
        Название модели в админ панели, таблица с данными
        """
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        db_table = 'app_categories'

    def get_absolute_url(self):
        """
        Получаем прямую ссылку на категорию
        """
        return reverse('post_by_category', kwargs={'slug': self.slug})

    def __str__(self):
        """
        Возвращение заголовка статьи
        """
        return self.title


class Comment(MPTTModel):
    """
    Модель древовидных комментариев
    """

    STATUS_OPTIONS = (
        ('published', 'Опубликовано'),
        ('draft', 'Черновик')
    )

    post = models.ForeignKey(Post, on_delete=models.CASCADE,
                             related_name='comments', verbose_name='Запись')
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='comments_author',
                               verbose_name='Автор комментария')
    content = models.TextField(max_length=3000,
                               verbose_name='Текст комментария')
    time_create = models.DateTimeField(auto_now_add=True,
                                       verbose_name='Время добавления')
    time_update = models.DateTimeField(auto_now=True,
                                       verbose_name='Время обновления')
    status = models.CharField(choices=STATUS_OPTIONS, default='published',
                              max_length=10, verbose_name='Статус комментария')
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children',
                            on_delete=models.CASCADE, verbose_name='Родительский комментарий')

    class MPTTMeta:
        """
        Сортировка по вложенности
        """
        order_insertion_by = ('-time_create',)

    class Meta:
        """
        Сортировка, название модели в админ панели, таблица в данными
        """
        ordering = ['-time_create']
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'

    def __str__(self):
        return f'{self.author}:{self.content}'


class Rating(models.Model):
    """
    Модель рейтинга: Лайк - Дизлайк
    """
    post = models.ForeignKey(Post, on_delete=models.CASCADE,
                             related_name='ratings', verbose_name='Запись')
    user = models.ForeignKey(User, on_delete=models.CASCADE,
                             blank=True, null=True, verbose_name='Пользователь')
    value = models.IntegerField(choices=[(1, 'Нравится'), (-1, 'Не нравится')],
                                verbose_name='Значение')
    time_create = models.DateTimeField(auto_now_add=True,
                                       verbose_name='Время добавления')
    ip_address = models.GenericIPAddressField(verbose_name='IP Адрес')

    class Meta:
        unique_together = ('post', 'ip_address')
        ordering = ('-time_create',)
        indexes = [models.Index(fields=['-time_create', 'value'])]
        verbose_name = 'Рейтинг'
        verbose_name_plural = 'Рейтинги'

    def __str__(self):
        return self.post.title
