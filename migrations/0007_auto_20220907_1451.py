# Generated by Django 3.2.15 on 2022-09-07 11:51

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('wagtailcore', '0066_collection_management_permissions'),
        ('commontail', '0006_auto_20220727_1915'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='authorhomepagerelation',
            name='commontail_authorhomepagerelation_unique_author_site_page',
        ),
        migrations.AlterField(
            model_name='authorhomepagerelation',
            name='author',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='home_page', to='commontail.author', verbose_name='author'),
        ),
        migrations.AlterField(
            model_name='authorhomepagerelation',
            name='page',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='wagtailcore.page', verbose_name='page'),
        ),
        migrations.AlterField(
            model_name='authorhomepagerelation',
            name='site',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='+', to='wagtailcore.site', verbose_name='site'),
        ),
        migrations.AlterField(
            model_name='namedreference',
            name='email',
            field=models.EmailField(blank=True, help_text='E-mail address to be used as a link.', max_length=254, verbose_name='e-mail address'),
        ),
        migrations.AddConstraint(
            model_name='authorhomepagerelation',
            constraint=models.UniqueConstraint(fields=('author', 'site'), name='commontail_authorhomepagerelation_unique_author_site'),
        ),
    ]