from django.db import models
from django.utils.translation import ugettext_lazy as _

from backend.settings import WEBAPP_URL
from ...constants import status


class AbstractBasePageTranslation(models.Model):
    """
    Data model representing a page or imprint page translation
    """

    #: Manage choices in :mod:`cms.constants.status`
    status = models.CharField(
        max_length=9,
        choices=status.CHOICES,
        default=status.DRAFT,
        verbose_name=_("status"),
    )
    currently_in_translation = models.BooleanField(
        default=False,
        verbose_name=_("currently in translation"),
        help_text=_(
            "Flag to indicate a translation is being updated by an external translator"
        ),
    )
    version = models.PositiveIntegerField(default=0, verbose_name=_("version"))
    minor_edit = models.BooleanField(
        default=False,
        verbose_name=_("minor edit"),
        help_text=_(
            "Tick if this change does not require an update of translations in other languages"
        ),
    )
    last_updated = models.DateTimeField(
        auto_now=True,
        verbose_name=_("modification date"),
    )

    @property
    def page(self):
        """
        The page the translation belongs to

        To be implemented in the inheriting model
        """
        raise NotImplementedError

    @property
    def language(self):
        """
        The language of the page translation

        To be implemented in the inheriting model
        """
        raise NotImplementedError

    @property
    def creator(self):
        """
        The user who created the page translation

        To be implemented in the inheriting model
        """
        raise NotImplementedError

    @property
    def permalink(self):
        """
        This property calculates the permalink dynamically

        To be implemented in the inheriting model
        """
        raise NotImplementedError

    @property
    def base_link(self):
        """
        This property calculates the page link without the slug dynamically

        To be implemented in the inheriting model
        """
        raise NotImplementedError

    @property
    def short_url(self):
        """
        This property calculates the short url dynamically

        To be implemented in the inheriting model
        """
        raise NotImplementedError

    @property
    def foreign_object(self):
        """
        This property is an alias of the page foreign key and is needed to generalize the :mod:`~cms.utils.slug_utils`
        for all content types

        :return: The page to which the translation belongs
        :rtype: ~cms.models.pages.page.Page
        """
        return self.page

    def get_absolute_url(self):
        """
        This helper function returns the absolute url to the webapp view of the page translation

        :return: The absolute url of a page translation
        :rtype: str
        """
        return "/" + self.permalink

    @property
    def available_languages(self):
        """
        This property checks in which :class:`~cms.models.languages.language.Language` the page is translated apart
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

        :return: A dictionary containing the available languages of a page translation
        :rtype: dict
        """
        languages = self.page.languages.exclude(id=self.language.id)
        available_languages = {}
        for language in languages:
            other_translation = self.page.get_public_translation(language.slug)
            if other_translation:
                available_languages[language.slug] = {
                    "id": other_translation.id,
                    "url": other_translation.permalink,
                }
        return available_languages

    @property
    def sitemap_alternates(self):
        """
        This property returns the language alternatives of a page translation for the use in sitemaps.
        Similar to :func:`cms.models.pages.abstract_base_page_translation.AbstractBasePageTranslation.available_languages`,
        but in a slightly different format.

        :return: A list of dictionaries containing the alternative translations of a page translation
        :rtype: list [ dict ]
        """
        languages = self.page.languages.exclude(id=self.language.id)
        available_languages = []
        for language in languages:
            other_translation = self.page.get_public_translation(language.slug)
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

        :return: The page translation in the source :class:`~cms.models.languages.language.Language` (:obj:`None` if
                 the translation is in the :class:`~cms.models.regions.region.Region`'s default
                 :class:`~cms.models.languages.language.Language`)
        :rtype: ~cms.models.pages.page_translation.PageTranslation
        """
        source_language_tree_node = self.page.region.language_tree_nodes.get(
            language=self.language
        ).parent
        if source_language_tree_node:
            return self.page.get_translation(source_language_tree_node.slug)
        return None

    @property
    def latest_public_revision(self):
        """
        This property is a link to the most recent public version of this translation.
        If the translation itself is not public, this property can return a revision which is older than ``self``.

        :return: The latest public revision of the translation
        :rtype: ~cms.models.pages.page_translation.PageTranslation
        """
        return self.page.translations.filter(
            language=self.language,
            status=status.PUBLIC,
        ).first()

    @property
    def latest_major_revision(self):
        """
        This property is a link to the most recent major version of this translation.

        :return: The latest major revision of the translation
        :rtype: ~cms.models.pages.page_translation.PageTranslation
        """
        return self.page.translations.filter(
            language=self.language,
            minor_edit=False,
        ).first()

    @property
    def latest_major_public_revision(self):
        """
        This property is a link to the most recent major public version of this translation.
        This is used when translations, which are derived from this translation, check whether they are up to date.

        :return: The latest major public revision of the translation
        :rtype: ~cms.models.pages.page_translation.PageTranslation
        """
        return self.page.translations.filter(
            language=self.language,
            status=status.PUBLIC,
            minor_edit=False,
        ).first()

    @property
    def previous_revision(self):
        """
        This property is a shortcut to the previous revision of this translation

        :return: The previous translation
        :rtype: ~cms.models.pages.page_translation.PageTranslation
        """
        version = self.version - 1
        return self.page.translations.filter(
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
        # If the page translation is currently in translation, it is defined as not outdated
        if self.currently_in_translation:
            return False
        return self.is_outdated_helper

    @property
    def is_outdated_helper(self):
        """
        See :meth:`~cms.models.pages.abstract_base_page_translation.AbstractBasePageTranslation.is_outdated` with the
        difference that it does not return ``False`` when ``currently_in_translation`` is ``True``.

        :return: Flag to indicate whether the translation is outdated
        :rtype: bool
        """
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
        This overwrites the default Django :meth:`~django.db.models.Model.__str__` method which would return ``AbstractBasePageTranslation object (id)``.
        It is used in the Django admin backend and as label for ModelChoiceFields.

        :return: A readable string representation of the page translation
        :rtype: str
        """
        # pylint: disable=no-member
        return self.title

    def __repr__(self):
        """
        This overwrites the default Django ``__repr__()`` method which would return ``<AbstractBasePageTranslation: AbstractBasePageTranslation object (id)>``.
        It is used for logging.

        :return: The canonical string representation of the page translation
        :rtype: str
        """
        class_name = type(self).__name__
        return f"<{class_name} (id: {self.id}, page_id: {self.page.id}, language: {self.language.slug}, slug: {self.slug})>"

    class Meta:
        #: The verbose name of the model
        verbose_name = _("page translation")
        #: The plural verbose name of the model
        verbose_name_plural = _("page translations")
        #: The fields which are used to sort the returned objects of a QuerySet
        ordering = ["page", "-version"]
        #: This model is an abstract base class
        abstract = True
