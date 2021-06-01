import logging

from django.core.serializers import base

from cms.models import Language, Page, PageTranslation

from . import base_serializer


logger = logging.getLogger(__name__)


class Serializer(base_serializer.Serializer):
    """
    XLIFF serializer class for XLIFF version 2.0

    Serializes :class:`~cms.models.pages.page_translation.PageTranslation` objects into translatable XLIFF files.
    """

    #: The source language of this serializer instance
    source_language = None
    #: The target language of this serializer instance
    target_language = None

    def serialize(self, queryset, *args, **kwargs):
        """
        Initialize serialization and find out in which source and target language the given elements are.
        """
        # Get all language objects of the given page translations
        language_set = set(map(lambda p: p.language, queryset))
        logger.debug("XLIFF 2.0 serialization for languages %r", language_set)
        if not language_set:
            raise base.SerializationError("No page translations given to serialize.")
        if len(language_set) != 1:
            raise base.SerializationError(
                "The page translations have different languages, but in XLIFF 2.0 all objects of one file need to have the same language."
            )

        # Get all region objects of the given page translations
        region_set = set(map(lambda p: p.page.region, queryset))
        logger.debug("XLIFF 2.0 serialization for regions %r", region_set)
        if len(region_set) != 1:
            raise base.SerializationError(
                "The page translations are from different regions."
            )

        region = next(iter(region_set))
        target_language = next(iter(language_set))
        if target_language == region.default_language:
            raise base.SerializationError(
                "The page translation is in the region's default language."
            )
        self.target_language = target_language
        logger.debug("XLIFF 2.0 serialization target language %r", target_language)
        self.source_language = target_language.get_source_language(region)
        logger.debug("XLIFF 2.0 serialization source language %r", self.source_language)
        return super().serialize(queryset, *args, **kwargs)

    def start_serialization(self):
        """
        Start serialization - open the XML document and the root element.
        """
        logger.debug(
            "XLIFF 2.0 starting serialization",
        )
        super().start_serialization()
        self.xml.startElement(
            "xliff",
            {
                "version": "2.0",
                "xmlns": "urn:oasis:names:tc:xliff:document:2.0",
                "srcLang": self.source_language.slug,
                "srcDir": self.source_language.text_direction,
                "trgLang": self.target_language.slug,
                "trgDir": self.target_language.text_direction,
            },
        )

    def start_object(self, obj):
        """
        Called as each object is handled.
        Adds an XLIFF ``<file>``-block with meta-information about the object.
        """
        logger.debug("XLIFF 2.0 serialization starting object %r", obj)
        self.xml.startElement(
            "file",
            {
                "original": str(obj.page.id),
            },
        )

    def handle_field(self, obj, field):
        """
        Called to handle each field on an object (except for ForeignKeys and ManyToManyFields)
        """
        logger.debug(
            "XLIFF 2.0 serialization handling field %r of object %r", field, obj
        )
        attrs = {
            "id": field.name,
            "resname": field.name,
            "restype": "string",
            "datatype": "html",
        }
        self.xml.startElement("unit", attrs)
        self.xml.startElement("segment", {})

        self.xml.startElement("source", {})
        source_translation = obj.source_translation
        if not source_translation:
            raise base.SerializationError(
                f"Page translation {obj!r} does not have a source translation in "
                f"{self.source_language!r} and therefore cannot be serialized to XLIFF."
            )
        logger.debug("XLIFF 2.0 source translation %r", source_translation)
        self.xml.cdata(field.value_to_string(source_translation))
        self.xml.endElement("source")

        self.xml.startElement("target", {})
        self.xml.cdata(field.value_to_string(obj))
        self.xml.endElement("target")

        self.xml.endElement("segment")
        self.xml.endElement("unit")

    def end_object(self, obj):
        """
        Called after handling all fields for an object.
        Ends the ``<file>``-block.
        """
        logger.debug("XLIFF 2.0 serialization ending object %r", obj)
        self.xml.endElement("file")


# pylint: disable=too-few-public-methods
class Deserializer(base_serializer.Deserializer):
    """
    XLIFF deserializer class for XLIFF version 2.0

    Deserializes XLIFF files into :class:`~cms.models.pages.page_translation.PageTranslation` objects.
    """

    def __init__(self, *args, **kwargs):
        # Initialize base serializer
        super().__init__(*args, **kwargs)
        # Get language objects from <xliff>-node
        for event, node in self.event_stream:
            if event == "START_ELEMENT" and node.nodeName == "xliff":
                try:
                    self.source_language = Language.objects.get(
                        slug=node.getAttribute("srcLang")
                    )
                    print(self.source_language)
                    self.target_language = Language.objects.get(
                        slug=node.getAttribute("trgLang")
                    )
                    print(self.target_language)
                    return
                except Language.DoesNotExist as e:
                    logger.exception(e)
                    raise base.DeserializationError(
                        "The language does not exist"
                    ) from e
        raise base.DeserializationError(
            "The XLIFF file does not contain an <xliff>-block,"
        )

    def _handle_object(self, node):
        """
        Convert a ``<file>``-node to a ``DeserializedObject``.
        """

        # Start building a data dictionary from the object.
        # If the node is missing the pk set it to None

        # data = {}
        original = node.getAttribute("original")
        try:
            page_id = int(original)
        except ValueError as e:
            raise base.DeserializationError(
                "The 'original' attribute of the <file>-block is not an integer"
            ) from e
        page = Page.objects.get(id=page_id)

        page_translation = page.get_translation(self.target_language.slug)
        if page_translation:
            page_translation.version = page_translation.version + 1
        else:
            page_translation = page.get_translation(self.source_language.slug)
        page_translation.id = None

        # Deseralize each field.
        for field_node in node.getElementsByTagName("unit"):

            field_name = field_node.getAttribute("resname")
            if not field_name:
                raise base.DeserializationError(
                    "<unit> node is missing the 'resname' attribute"
                )

            # Get the field from the PageTranslation model. This will raise a
            # FieldDoesNotExist if, well, the field doesn't exist, which will
            # be propagated correctly.
            try:
                field = PageTranslation._meta.get_field(field_name)
            except e:
                raise base.DeserializationError(
                    f"Field {field_name} does not exist in the PageTranslation model."
                ) from e

            target = field_node.getElementsByTagName("target")
            if len(target) != 1:
                raise base.DeserializationError(
                    f"Field {field_name} does not contain exactly one <target> node."
                )

            setattr(
                page_translation,
                field_name,
                field.to_python(self.getInnerText(target[0]).strip()),
            )

        # Return a DeserializedObject so that the m2m data has a place to live.
        return base.DeserializedObject(page_translation)
