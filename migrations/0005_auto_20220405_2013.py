# Generated by Django 3.2.12 on 2022-04-05 17:13

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('wagtailcore', '0066_collection_management_permissions'),
        ('commontail', '0004_pageviewscounter'),
    ]

    operations = [
        migrations.CreateModel(
            name='Author',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email', models.EmailField(blank=True, help_text="Author's public e-mail.", max_length=254, verbose_name='e-mail')),
                ('first_name', models.CharField(help_text="Author's first name.", max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(help_text="Author's last name.", max_length=150, verbose_name='last name')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'author',
                'verbose_name_plural': 'authors',
            },
        ),
        migrations.CreateModel(
            name='AuthorHomePageRelation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('author', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='home_page', to='commontail.author')),
                ('page', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='wagtailcore.page')),
                ('site', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='wagtailcore.site')),
            ],
            options={
                'verbose_name': 'author home page',
                'verbose_name_plural': 'authors home pages',
            },
        ),
        migrations.AddConstraint(
            model_name='authorhomepagerelation',
            constraint=models.UniqueConstraint(fields=('author', 'site', 'page'), name='commontail_authorhomepagerelation_unique_author_site_page'),
        ),
        migrations.AddConstraint(
            model_name='author',
            constraint=models.UniqueConstraint(fields=('first_name', 'last_name', 'email'), name='commontail_author_unique_author'),
        ),
    ]
