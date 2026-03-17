from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('movies', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='IMDbMovie',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tconst', models.CharField(max_length=16, unique=True)),
                ('title', models.CharField(max_length=255)),
                ('original_title', models.CharField(blank=True, max_length=255)),
                ('year', models.IntegerField(blank=True, null=True)),
                ('language', models.CharField(default='unknown', max_length=16)),
                ('countries', models.CharField(blank=True, max_length=128)),
                ('genres', models.JSONField(default=list)),
                ('rating', models.DecimalField(blank=True, decimal_places=1, max_digits=3, null=True)),
                ('votes', models.IntegerField(default=0)),
                ('plot', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'ordering': ['-votes', '-rating', 'title'],
            },
        ),
    ]
