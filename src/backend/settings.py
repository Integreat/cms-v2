"""
Django settings for ``integreat-cms``.

This file only contains the options which deviate from the default values.
For the full list of settings and their values, see :doc:`django:ref/settings`.

For production use, the following settings can be set with environment variables (use the prefix ``DJANGO_``):

    * ``DJANGO_SECRET_KEY``: :attr:`~backend.settings.SECRET_KEY`
    * ``DJANGO_DEBUG``: :attr:`~backend.settings.DEBUG`
    * ``DJANGO_LOGFILE``: :attr:`~backend.settings.LOGFILE`
    * ``DJANGO_WEBAPP_URL``: :attr:`~backend.settings.WEBAPP_URL`
    * ``DJANGO_MATOMO_URL``: :attr:`~backend.settings.MATOMO_URL`
    * ``DJANGO_BASE_URL``: :attr:`~backend.settings.BASE_URL`
    * ``DJANGO_STATIC_ROOT``: :attr:`~backend.settings.STATIC_ROOT`
    * ``DJANGO_MEDIA_ROOT``: :attr:`~backend.settings.MEDIA_ROOT`

Database settings: :attr:`~backend.settings.DATABASES`

    * ``DJANGO_DB_HOST``
    * ``DJANGO_DB_NAME``
    * ``DJANGO_DB_PASSWORD``
    * ``DJANGO_DB_USER``
    * ``DJANGO_DB_PORT``

Email settings:

    * ``DJANGO_EMAIL_HOST``: :attr:`~backend.settings.EMAIL_HOST`
    * ``DJANGO_EMAIL_HOST_PASSWORD``: :attr:`~backend.settings.EMAIL_HOST_PASSWORD`
    * ``DJANGO_EMAIL_HOST_USER``: :attr:`~backend.settings.EMAIL_HOST_USER`
    * ``DJANGO_EMAIL_PORT``: :attr:`~backend.settings.EMAIL_PORT`

"""
import os
import urllib

from .logging_formatter import ColorFormatter


###################
# CUSTOM SETTINGS #
###################

#: Build paths inside the project like this: ``os.path.join(BASE_DIR, ...)``
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

#: Version number
VERSION = "0.0.14"

if "DJANGO_WEBAPP_URL" in os.environ:
    WEBAPP_URL = os.environ["DJANGO_WEBAPP_URL"]
else:
    #: The URL to our webapp. This is used for urls in the ``sitemap.xml`` (see :mod:`sitemap` for more information).
    WEBAPP_URL = "https://integreat.app"

if "DJANGO_MATOMO_URL" in os.environ:
    MATOMO_URL = os.environ["DJANGO_MATOMO_URL"]
else:
    #: The URL to the Matomo statistics server.
    MATOMO_URL = "https://statistics.integreat-app.de"

#: The slug for the legal notice (see e.g. :class:`~cms.models.pages.imprint_page_translation.ImprintPageTranslation`)
IMPRINT_SLUG = "imprint"

#: The ID of the region "Testumgebung" - prevent sending PNs to actual users in development in
#: :func:`~cms.views.push_notifications.push_notification_sender.PushNotificationSender.send_pn`
TEST_BLOG_ID = 154

#: URL to the Integreat Website
WEBSITE_URL = "https://integreat-app.de"

#: An alias of :attr:`~backend.settings.WEBAPP_URL`. Used by django-linkcheck to determine whether a link is internal.
SITE_DOMAIN = WEBAPP_URL

#: URLs to the Integreat blog
BLOG_URLS = {
    "en": f"{WEBSITE_URL}/en/blog/",
    "de": f"{WEBSITE_URL}/blog/",
}

#: URL to the Integreat wiki
WIKI_URL = "https://wiki.integreat-app.de"

#: RSS feed URLs to the Integreat blog
RSS_FEED_URLS = {
    "en": f"{WEBSITE_URL}/en/feed/",
    "de": f"{WEBSITE_URL}/feed/",
}

#: How many days of chat history should be shown
AUTHOR_CHAT_HISTORY_DAYS = 30

###############################
# Firebase Push Notifications #
###############################

#: Authentification Token for the Firebase API. This needs to be set for a correct usage of the Messages Feature.
FCM_KEY = ""

###########
# GVZ API #
###########

#: Whether or not the GVZ (Gemeindeverzeichnis) API is enabled. This is used to automatically import coordinates and
#: region aliases (see :mod:`gvz_api` for more information).
GVZ_API_ENABLED = True

#: The URL to our GVZ (Gemeindeverzeichnis) API. This is used to automatically import coordinates and region aliases
#: (see :mod:`gvz_api` for more information).
GVZ_API_URL = "https://gvz.integreat-app.de"


############
# WEBAUTHN #
############

if "DJANGO_BASE_URL" in os.environ:
    HOSTNAME = urllib.parse.urlparse(os.environ["DJANGO_BASE_URL"]).netloc
    BASE_URL = os.environ["DJANGO_BASE_URL"]
else:
    #: Needed for `webauthn <https://pypi.org/project/webauthn/>`__
    #: (this is a setting in case the application runs behind a proxy).
    #: Used in the following views:
    #:
    #: - :class:`~cms.views.settings.mfa.register_user_mfa_key_view.RegisterUserMfaKeyView`
    #: - :class:`~cms.views.authentication.mfa.mfa_verify_view.MfaVerifyView`
    BASE_URL = "http://localhost:8000"
    #: Needed for `webauthn <https://pypi.org/project/webauthn/>`__
    #: (this is a setting in case the application runs behind a proxy).
    #: Used in the following views:
    #:
    #: - :class:`~cms.views.settings.mfa.get_mfa_challenge_view.GetMfaChallengeView`
    #: - :class:`~cms.views.settings.mfa.register_user_mfa_key_view.RegisterUserMfaKeyView`
    #: - :class:`~cms.views.authentication.mfa.mfa_assert_view.MfaAssertView`
    #: - :class:`~cms.views.authentication.mfa.mfa_verify_view.MfaVerifyView`
    HOSTNAME = "localhost"


########################
# DJANGO CORE SETTINGS #
########################

if "DJANGO_DEBUG" in os.environ:
    DEBUG = bool(os.environ["DJANGO_DEBUG"])
else:
    #: A boolean that turns on/off debug mode (see :setting:`django:DEBUG`)
    #:
    #: .. warning::
    #:     Never deploy a site into production with :setting:`DEBUG` turned on!
    DEBUG = True

#: Enabled applications (see :setting:`django:INSTALLED_APPS`)
INSTALLED_APPS = [
    "cms.apps.CmsConfig",
    "gvz_api.apps.GvzApiConfig",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.messages",
    "django.contrib.sessions",
    "django.contrib.sitemaps",
    "django.contrib.staticfiles",
    "corsheaders",
    "widget_tweaks",
    "easy_thumbnails",
    "filer",
    "mptt",
    "rules.apps.AutodiscoverRulesConfig",
    "linkcheck",
    "xliff",
]

# The default Django Admin application will only be activated if the system is in debug mode.
if DEBUG:
    INSTALLED_APPS.append("django.contrib.admin")

#: Activated middlewares (see :setting:`django:MIDDLEWARE`)
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "cms.middleware.timezone_middleware.TimezoneMiddleware",
]

#: Default URL dispatcher (see :setting:`django:ROOT_URLCONF`)
ROOT_URLCONF = "backend.urls"

#: Config for HTML templates (see :setting:`django:TEMPLATES`)
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "backend.context_processors.region_slug_processor",
            ],
            "debug": DEBUG,
        },
    },
]

#: WSGI (Web Server Gateway Interface) config (see :setting:`django:WSGI_APPLICATION`)
WSGI_APPLICATION = "backend.wsgi.application"


############
# DATABASE #
############

if (
    "DJANGO_DB_HOST" in os.environ
    and "DJANGO_DB_NAME" in os.environ
    and "DJANGO_DB_PASSWORD" in os.environ
    and "DJANGO_DB_USER" in os.environ
    and "DJANGO_DB_PORT" in os.environ
):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql_psycopg2",
            "NAME": os.environ["DJANGO_DB_NAME"],
            "USER": os.environ["DJANGO_DB_USER"],
            "PASSWORD": os.environ["DJANGO_DB_PASSWORD"],
            "HOST": os.environ["DJANGO_DB_HOST"],
            "PORT": os.environ["DJANGO_DB_PORT"],
        }
    }
else:
    #: A dictionary containing the settings for all databases to be used with this Django installation
    #: (see :setting:`django:DATABASES`)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql_psycopg2",
            "NAME": "integreat",
            "USER": "integreat",
            "PASSWORD": "password",
            "HOST": "localhost",
            "PORT": "5432",
        }
    }

#: Directory for initial database contents (see :setting:`django:FIXTURE_DIRS`)
FIXTURE_DIRS = (os.path.join(BASE_DIR, "cms/fixtures/"),)

#: Default primary key field type to use for models that don’t have a field with
#: :attr:`primary_key=True <django.db.models.Field.primary_key>`. (see :setting:`django:DEFAULT_AUTO_FIELD`)
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


############
# SECURITY #
############

if "DJANGO_BASE_URL" in os.environ:
    ALLOWED_HOSTS = [urllib.parse.urlparse(os.environ["DJANGO_BASE_URL"]).netloc]
else:
    #: This is a security measure to prevent HTTP Host header attacks, which are possible even under many seemingly-safe
    #: web server configurations (see :setting:`django:ALLOWED_HOSTS` and :ref:`django:host-headers-virtual-hosting`)
    ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]

#: A list of IP addresses, as strings, that allow the :func:`~django.template.context_processors.debug` context
#: processor to add some variables to the template context.
INTERNAL_IPS = ["localhost", "127.0.0.1"]

if "DJANGO_SECRET_KEY" in os.environ:
    SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
else:
    #: The secret key for this particular Django installation (see :setting:`django:SECRET_KEY`)
    #:
    #: .. warning::
    #:     Change the key in production and keep it secret!
    SECRET_KEY = "-!v282$zj815_q@htaxcubylo)(l%a+k*-xi78hw*#s2@i86@_"

#: A dotted path to the view function to be used when an incoming request is rejected by the CSRF protection
#: (see :setting:`django:CSRF_FAILURE_VIEW`)
CSRF_FAILURE_VIEW = "cms.views.error_handler.csrf_failure"


################
# CORS HEADERS #
################

#: Allow access to all domains by setting the following variable to ``True``
#: (see `django-cors-headers/ <https://pypi.org/project/django-cors-headers/>`__)
CORS_ORIGIN_ALLOW_ALL = True

#: Extend default headers with development header to differenciate dev traffic in statistics
#: (see `django-cors-headers/ <https://pypi.org/project/django-cors-headers/>`__)
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
    "x-integreat-development",
]


##################
# AUTHENTICATION #
##################

#: A list of authentication backend classes (as strings) to use when attempting to authenticate a user
#: (see :setting:`django:AUTHENTICATION_BACKENDS` and :ref:`django:authentication-backends`)
AUTHENTICATION_BACKENDS = (
    "rules.permissions.ObjectPermissionBackend",
    "django.contrib.auth.backends.ModelBackend",  # this is default
)

#: The list of validators that are used to check the strength of user’s passwords
#: (see :setting:`django:AUTH_PASSWORD_VALIDATORS` and :ref:`django:password-validation`)
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

#: The URL where requests are redirected for login (see :setting:`django:LOGIN_URL`)
LOGIN_URL = "/login"

#: The URL where requests are redirected after login (see :setting:`django:LOGIN_REDIRECT_URL`)
LOGIN_REDIRECT_URL = "/"

#: The URL where requests are redirected after logout (see :setting:`django:LOGOUT_REDIRECT_URL`)
LOGOUT_REDIRECT_URL = "/login"


###########
# LOGGING #
###########

#: The log level for integreat-cms django apps
LOG_LEVEL = "DEBUG" if DEBUG else "INFO"

#: The log level for the syslog
SYS_LOG_LEVEL = "INFO"

#: The log level for dependencies
DEPS_LOG_LEVEL = "INFO" if DEBUG else "WARN"

#: The default location of the logfile
DEFAULT_LOGFILE = "/var/log/integreat-cms.log"

if "DJANGO_LOGFILE" in os.environ and os.access(os.environ["DJANGO_LOGFILE"], os.W_OK):
    LOGFILE = os.environ["DJANGO_LOGFILE"]
elif DEBUG or not os.access(DEFAULT_LOGFILE, os.W_OK):
    #: The file path of the logfile. Needs to be writable by the application.
    #: Defaults to :attr:`~backend.settings.DEFAULT_LOGFILE`.
    LOGFILE = os.path.join(BASE_DIR, "integreat-cms.log")
else:
    LOGFILE = DEFAULT_LOGFILE

#: Logging configuration dictionary (see :setting:`django:LOGGING`)
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "console": {
            "format": "{asctime} \x1b[1m{levelname}\x1b[0m {name} - {message}",
            "datefmt": "%b %d %H:%M:%S",
            "style": "{",
        },
        "console-colored": {
            "()": ColorFormatter,
            "format": "{asctime} {levelname} {name} - {message}",
            "datefmt": "%b %d %H:%M:%S",
            "style": "{",
        },
        "logfile": {
            "format": "{asctime} {levelname:7} {name} - {message}",
            "datefmt": "%b %d %H:%M:%S",
            "style": "{",
        },
        "syslog": {
            "format": "INTEGREAT CMS - {levelname}: {message}",
            "style": "{",
        },
        "email": {
            "format": "Date and time: {asctime}\nSeverity: {levelname}\nLogger: {name}\nMessage: {message}\nFile: {funcName}() in {pathname}:{lineno}",
            "datefmt": "%Y-%m-%d %H:%M:%S",
            "style": "{",
        },
    },
    "filters": {
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        },
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
    },
    "handlers": {
        "console": {
            "filters": ["require_debug_true"],
            "class": "logging.StreamHandler",
            "formatter": "console",
        },
        "console-colored": {
            "filters": ["require_debug_true"],
            "class": "logging.StreamHandler",
            "formatter": "console-colored",
        },
        "logfile": {
            "class": "logging.FileHandler",
            "filename": LOGFILE,
            "formatter": "logfile",
        },
        "authlog": {
            "filters": ["require_debug_false"],
            "class": "logging.handlers.SysLogHandler",
            "address": "/dev/log",
            "facility": "auth",
            "formatter": "syslog",
        },
        "syslog": {
            "filters": ["require_debug_false"],
            "class": "logging.handlers.SysLogHandler",
            "address": "/dev/log",
            "facility": "syslog",
        },
        "mail_admins": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "django.utils.log.AdminEmailHandler",
            "formatter": "email",
        },
    },
    "loggers": {
        # Loggers of integreat-cms django apps
        "api": {
            "handlers": ["console-colored", "logfile", "mail_admins"],
            "level": LOG_LEVEL,
        },
        "backend": {
            "handlers": ["console-colored", "logfile", "mail_admins"],
            "level": LOG_LEVEL,
        },
        "cms": {
            "handlers": ["console-colored", "logfile", "mail_admins"],
            "level": LOG_LEVEL,
        },
        "gvz_api": {
            "handlers": ["console-colored", "logfile", "mail_admins"],
            "level": LOG_LEVEL,
        },
        "sitemap": {
            "handlers": ["console-colored", "logfile", "mail_admins"],
            "level": LOG_LEVEL,
        },
        "xliff": {
            "handlers": ["console-colored", "logfile", "mail_admins"],
            "level": LOG_LEVEL,
        },
        # Syslog for authentication
        "auth": {
            "handlers": ["console", "logfile", "authlog", "syslog"],
            "level": SYS_LOG_LEVEL,
        },
        # Loggers of dependencies
        "aiohttp.client": {
            "handlers": ["console", "logfile"],
            "level": DEPS_LOG_LEVEL,
        },
        "django": {
            "handlers": ["console", "logfile"],
            "level": DEPS_LOG_LEVEL,
        },
        "filer": {
            "handlers": ["console", "logfile"],
            "level": DEPS_LOG_LEVEL,
        },
        "PIL": {
            "handlers": ["console", "logfile"],
            "level": DEPS_LOG_LEVEL,
        },
        "requests": {
            "handlers": ["console", "logfile"],
            "level": DEPS_LOG_LEVEL,
        },
        "rules": {
            "handlers": ["console", "logfile"],
            "level": DEPS_LOG_LEVEL,
        },
        "urllib3": {
            "handlers": ["console", "logfile"],
            "level": DEPS_LOG_LEVEL,
        },
        "xhtml2pdf": {
            "handlers": ["console", "logfile"],
            "level": DEPS_LOG_LEVEL,
        },
    },
}


##########
# EMAILS #
##########

if DEBUG:
    #: The backend to use for sending emails (see :setting:`django:EMAIL_BACKEND` and :doc:`django:topics/email`)
    EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
else:
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"

#: Default email address to use for various automated correspondence from the site manager(s)
#: (see :setting:`django:DEFAULT_FROM_EMAIL`)
DEFAULT_FROM_EMAIL = "keineantwort@integreat-app.de"

#: The email address that error messages come from, such as those sent to :attr:`~backend.settings.ADMINS`.
#: (see :setting:`django:SERVER_EMAIL`)
SERVER_EMAIL = "keineantwort@integreat-app.de"

#: A list of all the people who get code error notifications. When :attr:`~backend.settings.DEBUG` is ``False``,
#: Django emails these people the details of exceptions raised in the request/response cycle.
ADMINS = [("Integreat Helpdesk", "tech@integreat-app.de")]

if "DJANGO_EMAIL_HOST" in os.environ:
    EMAIL_HOST = os.environ["DJANGO_EMAIL_HOST"]
else:
    #: The host to use for sending email.
    EMAIL_HOST = "localhost"

if "DJANGO_EMAIL_HOST_PASSWORD" in os.environ:
    EMAIL_HOST_PASSWORD = os.environ["DJANGO_EMAIL_HOST_PASSWORD"]
else:
    #: Password to use for the SMTP server defined in :attr:`~backend.settings.EMAIL_HOST`.
    #: If empty, Django won’t attempt authentication.
    EMAIL_HOST_PASSWORD = ""

if "DJANGO_EMAIL_HOST_USER" in os.environ:
    EMAIL_HOST_USER = os.environ["DJANGO_EMAIL_HOST_USER"]
else:
    #: Username to use for the SMTP server defined in :attr:`~backend.settings.EMAIL_HOST`.
    #: If empty, Django won’t attempt authentication.
    EMAIL_HOST_USER = ""

if "DJANGO_EMAIL_PORT" in os.environ:
    EMAIL_PORT = os.environ["DJANGO_EMAIL_PORT"]
else:
    #: Port to use for the SMTP server defined in :attr:`~backend.settings.EMAIL_HOST`.
    EMAIL_PORT = 25


########################
# INTERNATIONALIZATION #
########################

#: A list of all available languages (see :setting:`django:LANGUAGES` and :doc:`topics/i18n/index`)
LANGUAGES = (
    ("en", "English"),
    ("de", "Deutsch"),
)

#: A list of directories where Django looks for translation files
#: (see :setting:`django:LOCALE_PATHS` and :doc:`topics/i18n/index`)
LOCALE_PATHS = (os.path.join(BASE_DIR, "locale"),)

#: A string representing the language slug for this installation
#: (see :setting:`django:LANGUAGE_CODE` and :doc:`topics/i18n/index`)
LANGUAGE_CODE = "de"

#: A string representing the time zone for this installation
#: (see :setting:`django:TIME_ZONE` and :doc:`topics/i18n/index`)
TIME_ZONE = "UTC"

#: A string representing the time zone that is used for rendering
CURRENT_TIME_ZONE = "Europe/Berlin"

#: A boolean that specifies whether Django’s translation system should be enabled
#: (see :setting:`django:USE_I18N` and :doc:`topics/i18n/index`)
USE_I18N = True

#: A boolean that specifies if localized formatting of data will be enabled by default or not
#: (see :setting:`django:USE_L10N` and :doc:`topics/i18n/index`)
USE_L10N = True

#: A boolean that specifies if datetimes will be timezone-aware by default or not
#: (see :setting:`django:USE_TZ` and :doc:`topics/i18n/index`)
USE_TZ = True


################
# STATIC FILES #
################

if "DJANGO_STATIC_PARENT" in os.environ:
    STATIC_ROOT = os.environ["DJANGO_STATIC_ROOT"]
else:
    #: The absolute path to the directory where :mod:`django.contrib.staticfiles` will collect static files for
    #: deployment (see :setting:`django:STATIC_ROOT` and :doc:`Managing static files <django:howto/static-files/index>`)
    STATIC_ROOT = os.path.join(BASE_DIR, "cms/static/")

#: URL to use when referring to static files located in :setting:`STATIC_ROOT`
#: (see :setting:`django:STATIC_URL` and :doc:`Managing static files <django:howto/static-files/index>`)
STATIC_URL = "/static/"

#: The list of finder backends that know how to find static files in various locations
#: (see :setting:`django:STATICFILES_FINDERS`)
STATICFILES_FINDERS = (
    "django.contrib.staticfiles.finders.FileSystemFinder",
    "django.contrib.staticfiles.finders.AppDirectoriesFinder",
)

#: URL that handles the media served from :setting:`MEDIA_ROOT` (see :setting:`django:MEDIA_URL`)
MEDIA_URL = "/media/"


if "DJANGO_MEDIA_ROOT" in os.environ:
    MEDIA_ROOT = os.environ["DJANGO_MEDIA_ROOT"]
else:
    #: Absolute filesystem path to the directory that will hold user-uploaded files (see :setting:`django:MEDIA_ROOT`)
    MEDIA_ROOT = os.path.join(BASE_DIR, "media")


#: Defines the path element common to all canonical file URLs. (see :doc:`Django Filer Settings<django-filer:settings>`)
FILER_CANONICAL_URL = "media/"


#########
# CACHE #
#########

#: Configuration for PDF cache (see :setting:`django:CACHES`)
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.filebased.FileBasedCache",
        "LOCATION": os.path.join(STATIC_ROOT, "CACHE/django_cache"),
    }
}


###################
# EASY THUMBNAILS #
###################

#: Whether thumbnails should be stored in high resolution (used by :doc:`easy-thumbnails:index`)
THUMBNAIL_HIGH_RESOLUTION = True


##############
# PAGINATION #
##############

#: Number of entries displayed per pagination chunk
#: see :class:`~django.core.paginator.Paginator`
PER_PAGE = 16


####################
# DJANGO LINKCHECK #
####################

#: Disable linkcheck listeners e.g. when the fixtures are loaded
if "LINKCHECK_DISABLE_LISTENERS" in os.environ:
    LINKCHECK_DISABLE_LISTENERS = True


#############################
# Push Notification Channel #
#############################

CHANNELS = (("News", "News"),)


#######################
# XLIFF SERIALIZATION #
#######################

#: A dictionary of modules containing serializer definitions (provided as strings),
#: keyed by a string identifier for that serialization type (see :setting:`django:SERIALIZATION_MODULES`).
SERIALIZATION_MODULES = {
    "xliff": "xliff.generic_serializer",
    "xliff-1.2": "xliff.xliff1_serializer",
    "xliff-2.0": "xliff.xliff2_serializer",
}

#: The default fields to be used for the XLIFF serialization
XLIFF_DEFAULT_FIELDS = ("title", "text")

#: A mapping for changed field names to preserve backward compability after a database field was renamed
XLIFF_LEGACY_FIELDS = {"body": "text"}

#: The directory to which xliff files should be uploaded
XLIFF_UPLOAD_DIR = os.path.join(BASE_DIR, "xliff/upload/")

#: The directory from which xliff files should be downloaded
XLIFF_DOWNLOAD_DIR = os.path.join(BASE_DIR, "xliff/download/")

#: The URL path where XLIFF files are served for download
XLIFF_URL = "/xliff/"
