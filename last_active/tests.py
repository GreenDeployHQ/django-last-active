# Create your tests here.
import datetime
import time

import mock
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone
from last_active import middleware, settings
from last_active.models import LastActive, clear_interval, user_seen


class TestLastActiveModel(TestCase):
    def test_unicode(self):
        user = User(username="testuser")
        ts = datetime.datetime(2021, 1, 1, 2, 3, 4)
        seen = LastActive(user=user, last_active=ts)
        self.assertIn("testuser", str(seen))
        self.assertIn("2013-01-01 02:03:04", str(seen))


class TestLastActiveManager(TestCase):
    @mock.patch("last_active.models.LastActive.objects.get_or_create", autospec=True)
    def test_seen(self, get_or_create):
        user = User(username="testuser", pk=1)
        LastActive = mock.Mock(LastActive)
        get_or_create.return_value = (LastActive, True)

        LastActive.objects.seen(user=user)

        get_or_create.assert_called_with(
            user=user, module=settings.last_active_DEFAULT_MODULE, site=Site.objects.get_current()
        )
        self.assertFalse(LastActive.save.called)

    @mock.patch("last_active.models.LastActive.objects.get_or_create", autospec=True)
    def test_seen_no_default(self, get_or_create):
        user = User(username="testuser", pk=1)
        site = Site(pk=2)
        get_or_create.return_value = (None, True)

        LastActive.objects.seen(user=user, site=site, module="test")

        get_or_create.assert_called_with(user=user, module="test", site=site)

    @mock.patch("last_active.models.LastActive.objects.get_or_create", autospec=True)
    def test_seen_create(self, get_or_create):
        user = User(username="testuser")
        LastActive = mock.Mock(LastActive)
        get_or_create.return_value = (LastActive, True)

        LastActive.objects.seen(user=user)

        get_or_create.assert_called_with(
            user=user, module=settings.last_active_DEFAULT_MODULE, site=Site.objects.get_current()
        )
        self.assertFalse(LastActive.save.called)

    @mock.patch("last_active.models.LastActive.objects.get_or_create", autospec=True)
    def test_seen_update(self, get_or_create):
        user = User(username="testuser")
        LastActive = mock.Mock(LastActive)
        # force last seen old
        old_time = timezone.now() - datetime.timedelta(seconds=(settings.last_active_INTERVAL * 2))
        LastActive.last_active = old_time
        get_or_create.return_value = (LastActive, False)

        ret = LastActive.objects.seen(user=user)

        get_or_create.assert_called_with(
            user=user, module=settings.last_active_DEFAULT_MODULE, site=Site.objects.get_current()
        )
        self.assertTrue(LastActive.save.called)
        self.assertNotEqual(ret.last_active, old_time)

    @mock.patch("last_active.models.LastActive.objects.get_or_create", autospec=True)
    def test_seen_update_forced(self, get_or_create):
        user = User(username="testuser")
        LastActive = mock.Mock(LastActive)
        # force last seen old
        old_time = timezone.now()
        LastActive.last_active = old_time
        get_or_create.return_value = (LastActive, False)

        ret = LastActive.objects.seen(user=user, force=True)

        get_or_create.assert_called_with(
            user=user, module=settings.last_active_DEFAULT_MODULE, site=Site.objects.get_current()
        )
        self.assertTrue(LastActive.save.called)
        self.assertNotEqual(ret.last_active, old_time)

    @mock.patch("last_active.models.LastActive.objects.get_or_create", autospec=True)
    def test_seen_found_not_updated(self, get_or_create):
        user = User(username="testuser")
        LastActive = mock.Mock(LastActive)
        # force last seen old
        old_time = timezone.now()
        LastActive.last_active = old_time
        get_or_create.return_value = (LastActive, False)

        ret = LastActive.objects.seen(user=user)

        get_or_create.assert_called_with(
            user=user, module=settings.last_active_DEFAULT_MODULE, site=Site.objects.get_current()
        )
        self.assertFalse(LastActive.save.called)
        self.assertEqual(ret.last_active, old_time)

    def test_when_non_existent(self):
        user = User(username="testuser", pk=1)
        self.assertRaises(LastActive.DoesNotExist, LastActive.objects.when, user)

    @mock.patch("last_active.models.LastActive.objects.filter", autospec=True)
    def test_seen_defaults(self, filter):
        user = User(username="testuser")
        LastActive.objects.when(user=user)

        filter.assert_called_with(user=user)

    @mock.patch("last_active.models.LastActive.objects.filter", autospec=True)
    def test_seen_module(self, filter):
        user = User(username="testuser")
        LastActive.objects.when(user=user, module="mod")

        filter.assert_called_with(user=user, module="mod")

    @mock.patch("last_active.models.LastActive.objects.filter", autospec=True)
    def test_seen_site(self, filter):
        user = User(username="testuser")
        site = Site()
        LastActive.objects.when(user=user, site=site)

        filter.assert_called_with(user=user, site=site)


class TestUserSeen(TestCase):
    def setUp(self):
        [cache.delete(key) for key in list(cache._cache.keys())]

    @mock.patch("last_active.models.LastActive.objects.seen", autospec=True)
    def test_user_seen(self, seen):
        user = User(username="testuser", pk=999)

        user_seen(user)
        site = Site.objects.get_current()
        seen.assert_called_with(user, module=settings.last_active_DEFAULT_MODULE, site=site)

    @mock.patch("last_active.models.LastActive.objects.seen", autospec=True)
    def test_user_seen_no_default(self, seen):
        user = User(username="testuser", pk=1)
        site = Site(pk=2)
        user_seen(user, module="test", site=site)
        seen.assert_called_with(user, module="test", site=site)

    @mock.patch("last_active.models.LastActive.objects.seen", autospec=True)
    def test_user_seen_cached(self, seen):
        user = User(username="testuser", pk=1)
        module = "test_mod"
        cache.set("last_active:%s:%s" % (module, user.pk), time.time())
        user_seen(user, module=module)
        self.assertFalse(seen.called)

    @mock.patch("last_active.models.LastActive.objects.seen", autospec=True)
    def test_user_seen_cache_expired(self, seen):
        user = User(username="testuser", pk=1)
        module = "test_mod"
        cache.set(
            "last_active:%s:%s" % (module, user.pk),
            time.time() - (2 * settings.last_active_INTERVAL),
        )
        user_seen(user, module=module)
        site = Site.objects.get_current()
        seen.assert_called_with(user, module=module, site=site)


class TestClearInterval(TestCase):
    @mock.patch("last_active.models.LastActive.objects.filter", autospec=True)
    @mock.patch("last_active.models.cache", autospec=True)
    def test_clear_interval(self, cache, filter):
        site = Site.objects.get_current()
        user = User(username="testuser", pk=1)
        ls1 = LastActive(user=user, module="mod1", site=site)
        ls2 = LastActive(user=user, module="mod2", site=site)
        filter.return_value = [ls1, ls2]

        clear_interval(user)

        filter.assert_called_with(user=user)
        expected = {"last_active:1:mod1:1": -1, "last_active:1:mod2:1": -1}
        cache.set_many.assert_called_with(expected)

    @mock.patch("last_active.models.LastActive.objects.filter", autospec=True)
    @mock.patch("last_active.models.cache", autospec=True)
    def test_clear_interval_none(self, cache, filter):
        user = User(username="testuser", pk=1)
        filter.return_value = []

        clear_interval(user)

        filter.assert_called_with(user=user)
        self.assertFalse(cache.delete_many.called)

    def test_clear_interval_works(self):
        user = User.objects.create(username="testuser")

        user_seen(user)
        when1 = LastActive.objects.when(user=user)
        clear_interval(user)
        user_seen(user)
        when2 = LastActive.objects.when(user=user)

        self.assertNotEqual(when1, when2)


class TestMiddleware(TestCase):

    middleware = middleware.LastActiveMiddleware()

    @mock.patch("last_active.middleware.user_seen", autospec=True)
    def test_process_request(self, user_seen):
        request = mock.Mock()
        request.user.is_authenticated.return_value = False
        self.middleware.process_request(request)
        self.assertFalse(user_seen.called)

    @mock.patch("last_active.middleware.user_seen", autospec=True)
    def test_process_request_auth(self, user_seen):
        request = mock.Mock()
        request.user.is_authenticated.return_value = True
        self.middleware.process_request(request)
        user_seen.assert_called_with(request.user)
