# Generated by Django 3.2.4 on 2021-06-13 19:54

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('wagtailcore', '0062_comment_models_and_pagesubscription'),
        ('wagtailimages', '0023_add_choose_permissions'),
    ]

    operations = [
        migrations.CreateModel(
            name='Image',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('wagtailimages.image',),
        ),
        migrations.CreateModel(
            name='CommonSettings',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('docs_background', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='wagtailimages.image', verbose_name='printable docs background')),
                ('logo', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='wagtailimages.image', verbose_name='main logo')),
                ('logo_square', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='+', to='wagtailimages.image', verbose_name='square logo')),
                ('site', models.OneToOneField(editable=False, on_delete=django.db.models.deletion.CASCADE, to='wagtailcore.site')),
            ],
            options={
                'verbose_name': 'common',
                'verbose_name_plural': 'common',
            },
        ),
    ]
