from django.core.serializers import base

from cms.models import Page, PageTranslation

from . import base_serializer


class Serializer(base_serializer.Serializer):
    """
    XLIFF serializer class for XLIFF version 1.2.
    This was inspired by `django-xliff<https://github.com/callowayproject/django-xliff>`__.
    """

    def start_serialization(self):
        """
        Start serialization - open the XML document and the root element.
        """
        super().start_serialization()
        self.xml.startElement(
            "xliff",
            {
                "version": "1.2",
                "xmlns": "urn:oasis:names:tc:xliff:document:1.2",
            },
        )

    def start_object(self, obj):
        """
        Called as each object is handled.
        Adds an XLIFF ``<file>``-block with meta-information about the object and an additional ``<body>`` for XLIFF version 1.2.
        """
        source_language = obj.language.get_source_language(obj.region)
        if not source_language:
            raise base.SerializationError(
                "The page translation is in the region's default language."
            )
        self.xml.startElement(
            "file",
            {
                "original": str(obj.page.id),
                "datatype": "plaintext",
                "source-language": source_language.slug,
                "target-language": obj.language.slug,
            },
        )
        self.xml.startElement("body", {})

    def handle_field(self, obj, field):
        """
        Called to handle each field on an object (except for ForeignKeys and ManyToManyFields)
        """
        attrs = {
            "id": field.name,
            "resname": field.name,
            "restype": "string",
            "datatype": "html",
        }
        self.xml.startElement("trans-unit", attrs)

        self.xml.startElement("source", {})
        source_translation = obj.source_translation
        self.xml.cdata(field.value_to_string(source_translation))
        self.xml.endElement("source")

        self.xml.startElement("target", {})
        self.xml.cdata(field.value_to_string(obj))
        self.xml.endElement("target")

        self.xml.endElement("trans-unit")

    def end_object(self, obj):
        """
        Called after handling all fields for an object.
        Ends the ``<file>``-block.
        """
        self.xml.endElement("body")
        self.xml.endElement("file")


# pylint: disable=too-few-public-methods
class Deserializer(base_serializer.Deserializer):
    """
    XLIFF deserializer class for XLIFF version 1.2
    """

    # pylint: disable=too-many-locals
    def _handle_object(self, node):
        """
        Convert a ``<field>``-node to a ``DeserializedObject``.
        """

        # data = {}
        original = node.getAttribute("original")
        try:
            page_id = int(original)
        except ValueError as e:
            raise base.DeserializationError(
                "The 'original' attribute of the <file>-block is not an integer"
            ) from e
        page = Page.objects.get(id=page_id)

        source_language_slug = node.getAttribute("source-language")
        # source_language = Language.objects.get(slug=source_language_slug)

        target_language_slug = node.getAttribute("target-language")
        # target_language = Language.objects.get(slug=target_language_slug)

        page_translation = page.get_translation(language__slug=target_language_slug)
        if page_translation:
            page_translation.version = page_translation.version + 1
        else:
            page_translation = page.get_translation(language__slug=source_language_slug)

            page_translation.id = None

        # Deseralize each field.
        for field_node in node.getElementsByTagName("trans-unit"):

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
