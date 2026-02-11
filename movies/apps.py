from django.apps import AppConfig


class MoviesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'movies'
    
    def ready(self):
        """Auto-update site domain on startup for OAuth"""
        import os
        from django.contrib.sites.models import Site
        from django.db import connection
        
        # Only run if database is ready and not during migrations
        if 'django_site' in connection.introspection.table_names():
            try:
                # Get domain from environment variable or use first ALLOWED_HOST
                allowed_hosts = os.environ.get('ALLOWED_HOSTS', '').split(',')
                domain = os.environ.get('SITE_DOMAIN', allowed_hosts[0] if allowed_hosts else 'localhost')
                domain = domain.strip()
                
                if domain and domain != 'localhost':
                    site = Site.objects.get_or_create(id=1)[0]
                    if site.domain != domain:
                        site.domain = domain
                        site.name = 'Movie Recommender'
                        site.save()
            except Exception:
                pass  # Fail silently during migrations or if database isn't ready
