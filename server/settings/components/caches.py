from server.settings.components import env

# Caching
# https://docs.djangoproject.com/en/2.2/topics/cache/

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"{env.str('REDIS_URL')}?db=0",
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient",},
    }
}
