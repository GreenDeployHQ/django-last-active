# last_active

last_active is a Django app to track when a user is last active on a website. The last active time is kept on the database.

It was forked from `django-last-seen`.

The intention is to eventually add weekly active user tracking feature as well.


## Installation

1. Add "last_active" to your INSTALLED_APPS setting like this

```
    INSTALLED_APPS = [
        ...
        'last_active',
    ]
```

2. Add 'last_active.middleware.LastActiveMiddleware' to MIDDLEWARE_CLASSES tuple found in your settings file.

3. Run ``python manage.py migrate`` to create the last_active models.

## Settings

**LAST_SEEN_DEFAULT_MODULE**

The default module used on the middleware. The default value is default.

**LAST_SEEN_INTERVAL**

How often is the last seen timestamp updated to the database. The default is 2 hours.

**LAST_SEEN_SITE_MODEL**

Allows a different Site model to be used, introduced to allow for Wagtail Sites. If you are using wagtail, set this to ``wagtailcore.Site``. Defaults to the django ``Site`` model.