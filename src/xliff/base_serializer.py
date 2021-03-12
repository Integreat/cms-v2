"""
This module contains the abstract base classes for the XLIFF serializers.
It makes use of the existinng Django serialization functionality (see :doc:`django:topics/serialization` and
:ref:`django:topics/serialization:xml`).

It extends :django-source:`django/core/serializers/base.py` and
:django-source:`django/core/serializers/xml_serializer.py`.
"""
import xml.dom.minidom

from django.conf import settings
from django.core.serializers import xml_serializer
from django.utils.xmlutils import SimplerXMLGenerator

from backend.settings import XLIFF_DEFAULT_FIELDS


class XMLGeneratorWithCDATA(SimplerXMLGenerator):
    """
    Subclass of SimplerXMLGenerator to provide a custom CDATA node
    """

    def cdata(self, content):
        """
        Create a ``<![CDATA[]>``-block with the given content

        :param content: The given ``CDATA`` content
        :type content: str
        """
        self.ignorableWhitespace(f"<![CDATA[{content}]]>")


class Serializer(xml_serializer.Serializer):
    """
    Abstract base XLIFF serializer class. Inherits basic XML initialization from the default xml_serializer of Django
    (see :ref:`django:topics/serialization:xml`).

    The XLIFF file can be extended by writing to ``self.xml``, which is an instance of
    :class:`xliff.base_serializer.XMLGeneratorWithCDATA`.

    For details, look at the implementation of :django-source:`django/core/serializers/base.py` and
    :django-source:`django/core/serializers/xml_serializer.py`.
    """

    #: The XML generator of this serializer instance
    xml = None

    def serialize(self, queryset, *args, **kwargs):
        """
        Initialize serialization and set the :attr:`backend.settings.XLIFF_DEFAULT_FIELDS`.
        """
        kwargs.setdefault("fields", XLIFF_DEFAULT_FIELDS)
        return super().serialize(queryset, *args, **kwargs)

    def start_serialization(self):
        """
        Start serialization - open the XML document and the root element.
        """
        self.xml = XMLGeneratorWithCDATA(
            self.stream, self.options.get("encoding", settings.DEFAULT_CHARSET)
        )
        self.xml.startDocument()

    def start_object(self, obj):
        """
        Called when serializing of an object starts.
        """
        raise NotImplementedError(
            "subclasses of Serializer must provide a start_object() method"
        )

    def handle_field(self, obj, field):
        """
        Called to handle each field on an object (except for ForeignKeys and ManyToManyFields)
        """
        raise NotImplementedError(
            "subclasses of Serializer must provide a handle_field() method"
        )

    def handle_fk_field(self, obj, field):
        """
        ForeignKey fields are not supported by this serializer.
        They will just be ignored and are not contained in the resulting XLIFF file.
        """

    def handle_m2m_field(self, obj, field):
        """
        ManyToMany fields are not supported by this serializer.
        They will just be ignored and are not contained in the resulting XLIFF file.
        """

    def end_object(self, obj):
        """
        Called when serializing of an object ends.
        """

    def end_serialization(self):
        """
        End serialization by ending the ``<xliff>``-block and the document.
        """
        self.xml.endElement("xliff")
        self.xml.endDocument()

    def getvalue(self):
        """
        Return the fully serialized translation (or ``None`` if the output stream is not seekable).
        """
        if callable(getattr(self.stream, "getvalue", None)):
            # Pretty print output
            return xml.dom.minidom.parseString(self.stream.getvalue()).toprettyxml()
        return None


class Deserializer(xml_serializer.Deserializer):
    """
    Abstract base XLIFF deserializer class. Inherits basic XML initialization from the default xml_serializer of Django.
    The contents of the XLIFF file are available through ``self.event_stream``, which gets assigned to the result of
    :func:`python:xml.dom.pulldom.parse`.
    """

    def __next__(self):
        """
        Iteration iterface which returns the next item in the stream.
        Since each object has its own ``<file>``-block, this is where the XLIFF file gets splitted.
        """
        for event, node in self.event_stream:
            if event == "START_ELEMENT" and node.nodeName == "file":
                self.event_stream.expandNode(node)
                return self._handle_object(node)
        raise StopIteration

    def _handle_object(self, node):
        """
        Convert a ``<file>``-node to a ``DeserializedObject``.
        To be implemented in the subclass of this base serializer.
        """
        raise NotImplementedError(
            "subclasses of Serializer must provide a _handle_object() method"
        )

    @classmethod
    def getInnerText(cls, node):
        """
        Get all the inner text of a DOM node (recursively).
        """
        # inspired by http://mail.python.org/pipermail/xml-sig/2005-March/011022.html
        inner_text = []
        for child in node.childNodes:
            if (
                child.nodeType == child.TEXT_NODE
                or child.nodeType == child.CDATA_SECTION_NODE
            ):
                inner_text.append(child.data)
            elif child.nodeType == child.ELEMENT_NODE:
                inner_text.extend(cls.getInnerText(child))
            else:
                pass
        return "".join(inner_text)
