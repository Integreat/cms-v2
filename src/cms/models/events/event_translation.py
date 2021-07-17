from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.utils.translation import ugettext_lazy as _

from linkcheck.models import Link
from backend.settings import WEBAPP_URL

from .event import Event
from ..languages.language import Language
from ...constants import status
from ...utils.translation_utils import ugettext_many_lazy as __


class EventTranslation(models.Model):
    """
    Data model representing an event translation
    """

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name="translations",
        verbose_name=_("event"),
    )
    slug = models.SlugField(
        max_length=1024,
        allow_unicode=True,
        verbose_name=_("URL parameter"),
        help_text=__(
            _("String identifier without spaces and special characters."),
            _("Unique per region and language."),
            _("Leave blank to generate unique parameter from title."),
        ),
    )
    #: Manage choices in :mod:`cms.constants.status`
    status = models.CharField(
        max_length=9,
        choices=status.CHOICES,
        default=status.DRAFT,
        verbose_name=_("status"),
    )
    title = models.CharField(max_length=1024, verbose_name=_("title"))
    description = models.TextField(blank=True, verbose_name=_("description"))
    language = models.ForeignKey(
        Language,
        on_delete=models.CASCADE,
        related_name="event_translations",
        verbose_name=_("language"),
    )
    currently_in_translation = models.BooleanField(
        default=False,
        verbose_name=_("currently in translation"),
        help_text=_(
            "Flag to indicate a translation is being updated by an external translator"
        ),
    )
    version = models.PositiveIntegerField(default=0, verbose_name=_("revision"))
    minor_edit = models.BooleanField(
        default=False,
        verbose_name=_("minor edit"),
        help_text=_(
            "Tick if this change does not require an update of translations in other languages"
        ),
    )
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="event_translations",
        verbose_name=_("creator"),
    )
    last_updated = models.DateTimeField(
        auto_now=True,
        verbose_name=_("modification date"),
    )
    links = GenericRelation(Link, related_query_name="event_translations")

    @property
    def foreign_object(self):
        """
        This property is an alias of the event foreign key and is needed to generalize the :mod:`~cms.utils.slug_utils`
        for all content types

        :return: The event to which the translation belongs
        :rtype: ~cms.models.events.event.Event
        """
        return self.event

    @property
    def permalink(self):
        """
        This property calculates the permalink dynamically by joining the parent path together with the slug

        :return: The permalink of the event
        :rtype: str
        """
        return "/".join(
            [self.event.region.slug, self.language.slug, "events", self.slug]
        )

    def get_absolute_url(self):
        """
        This helper function returns the absolute url to the webapp view of the event translation

        :return: The absolute url of an event translation
        :rtype: str
        """
        return "/" + self.permalink

    @property
    def available_languages(self):
        """
        This property checks in which :class:`~cms.models.languages.language.Language` the event is translated apart
        from ``self.language``.
        It only returns languages which have a public translation, so drafts are not included here.
        The returned dict has the following format::

            {
                available_translation.language.slug: {
                    'id': available_translation.id,
                    'url': available_translation.permalink
                },
                ...
            }

        :return: A dictionary containing the available languages of an event translation
        :rtype: dict
        """
        languages = self.event.languages.exclude(id=self.language.id)
        available_languages = {}
        for language in languages:
            other_translation = self.event.get_public_translation(language.slug)
            if other_translation:
                available_languages[language.slug] = {
                    "id": other_translation.id,
                    "url": other_translation.permalink,
                }
        return available_languages

    @property
    def sitemap_alternates(self):
        """
        This property returns the language alternatives of a event translation for the use in sitemaps.
        Similar to :func:`cms.models.events.event_translation.EventTranslation.available_languages`, but in a slightly
        different format.

        :return: A list of dictionaries containing the alternative translations of a event translation
        :rtype: list [ dict ]
        """
        languages = self.event.languages.exclude(id=self.language.id)
        available_languages = []
        for language in languages:
            other_translation = self.event.get_public_translation(language.slug)
            if other_translation:
                available_languages.append(
                    {
                        "location": f"{WEBAPP_URL}{other_translation.get_absolute_url()}",
                        "lang_slug": other_translation.language.slug,
                    }
                )
        return available_languages

    @property
    def source_translation(self):
        """
        This property returns the translation which was used to create the ``self`` translation.
        It derives this information from the :class:`~cms.models.regions.region.Region`'s root
        :class:`~cms.models.languages.language_tree_node.LanguageTreeNode`.

        :return: The event translation in the source :class:`~cms.models.languages.language.Language` (:obj:`None` if
                 the translation is in the :class:`~cms.models.regions.region.Region`'s default
                 :class:`~cms.models.languages.language.Language`)
        :rtype: ~cms.models.events.event_translation.EventTranslation
        """
        source_language_tree_node = self.event.region.language_tree_nodes.get(
            language=self.language
        ).parent
        if source_language_tree_node:
            return self.event.get_translation(source_language_tree_node.slug)
        return None

    @property
    def latest_public_revision(self):
        """
        This property is a link to the most recent public version of this translation.
        If the translation itself is not public, this property can return a revision which is older than ``self``.

        :return: The latest public revision of the translation
        :rtype: ~cms.models.events.event_translation.EventTranslation
        """
        return self.event.translations.filter(
            language=self.language,
            status=status.PUBLIC,
        ).first()

    @property
    def latest_major_revision(self):
        """
        This property is a link to the most recent major version of this translation.

        :return: The latest major revision of the translation
        :rtype: ~cms.models.events.event_translation.EventTranslation
        """
        return self.event.translations.filter(
            language=self.language,
            minor_edit=False,
        ).first()

    @property
    def latest_major_public_revision(self):
        """
        This property is a link to the most recent major public version of this translation.
        This is used when translations, which are derived from this translation, check whether they are up to date.

        :return: The latest major public revision of the translation
        :rtype: ~cms.models.events.event_translation.EventTranslation
        """
        return self.event.translations.filter(
            language=self.language,
            status=status.PUBLIC,
            minor_edit=False,
        ).first()

    @property
    def previous_revision(self):
        """
        This property is a shortcut to the previous revision of this translation

        :return: The previous translation
        :rtype: ~cms.models.events.event_translation.EventTranslation
        """
        version = self.version - 1
        return self.event.translations.filter(
            language=self.language,
            version=version,
        ).first()

    @property
    def is_outdated(self):
        """
        This property checks whether a translation is outdated and thus needs a new revision of the content.
        This happens, when the source translation is updated and the update is no `minor_edit`.

        * If the translation is currently being translated, it is considered not outdated.
        * If the translation's language is the region's default language, it is defined to be never outdated.
        * If the translation's source translation is already outdated, then the translation itself also is.
        * If neither the translation nor its source translation have a latest major public translation, it is defined as
          not outdated.
        * If neither the translation nor its source translation have a latest major public translation, it is defined as
          not outdated.

        Otherwise, the outdated flag is calculated by comparing the `last_updated`-field of the translation and its
        source translation.

        :return: Flag to indicate whether the translation is outdated
        :rtype: bool
        """
        # If the event translation is currently in translation, it is defined as not outdated
        if self.currently_in_translation:
            return False
        source_translation = self.source_translation
        # If self.language is the root language, this translation can never be outdated
        if not source_translation:
            return False
        # If the source translation is outdated, this translation can not be up to date
        if source_translation.is_outdated:
            return True
        self_revision = self.latest_major_public_revision
        source_revision = source_translation.latest_major_public_revision
        # If one of the translations has no major public revision, it cannot be outdated
        if not self_revision or not source_revision:
            return False
        return self_revision.last_updated < source_revision.last_updated

    @property
    def is_up_to_date(self):
        """
        This property checks whether a translation is up to date.
        A translation is considered up to date when it is not outdated and not being translated at the moment.

        :return: Flag which indicates whether a translation is up to date
        :rtype: bool
        """
        return not self.currently_in_translation and not self.is_outdated

    def __str__(self):
        """
        This overwrites the default Django :meth:`~django.db.models.Model.__str__` method which would return ``EventTranslation object (id)``.
        It is used in the Django admin backend and as label for ModelChoiceFields.

        :return: A readable string representation of the event translation
        :rtype: str
        """
        return self.title

    def __repr__(self):
        """
        This overwrites the default Django ``__repr__()`` method which would return ``<EventTranslation: EventTranslation object (id)>``.
        It is used for logging.

        :return: The canonical string representation of the event translation
        :rtype: str
        """
        return f"<EventTranslation (id: {self.id}, event_id: {self.event.id}, language: {self.language.slug}, slug: {self.slug})>"

    class Meta:
        #: The verbose name of the model
        verbose_name = _("event translation")
        #: The plural verbose name of the model
        verbose_name_plural = _("event translations")
        #: The fields which are used to sort the returned objects of a QuerySet
        ordering = ["event", "-version"]
        #: The default permissions for this model
        default_permissions = ()
