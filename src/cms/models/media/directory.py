from django.db import models
from django.utils import timezone
from django.utils.formats import localize
from django.utils.translation import ugettext_lazy as _

from ..regions.region import Region


class Directory(models.Model):
    """
    Model representing a directory containing documents. This is only a virtual directory and does not necessarily
    exist on the actual file system. Each directory is tied to a region.
    """

    name = models.CharField(max_length=255, blank=False, verbose_name=_("name"))
    region = models.ForeignKey(
        Region,
        related_name="media_directories",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        verbose_name=_("region"),
    )
    parent = models.ForeignKey(
        "self",
        related_name="subdirectories",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        verbose_name=_("parent directory"),
    )
    created_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("creation date"),
        help_text=_("The date and time when the directory was created"),
    )

    def serialize(self):
        """
        This method creates a serialized version of that object for later use in AJAX and JSON.

        :return: The serialized representation of the directory
        :rtype: str
        """
        return {
            "type": "directory",
            "id": self.id,
            # Use empty string because preact-router only handles string parameters
            "parentId": self.parent.id if self.parent else "",
            "name": self.name,
            "CreatedDate": localize(timezone.localtime(self.created_date)),
            "isGlobal": not self.region,
            "numberOfEntries": self.subdirectories.count() + self.files.count(),
        }

    def __str__(self):
        """
        This overwrites the default Python __str__ method which would return <Directory object at 0xDEADBEEF>

        :return: The string representation (in this case the name) of the directory
        :rtype: str
        """
        return self.name

    def __repr__(self):
        """
        This overwrites the default Django ``__repr__()`` method which would return ``<Directory: Directory object (id)>``.
        It is used for logging.

        :return: The canonical string representation of the directory
        :rtype: str
        """
        region = f"region: {self.region.slug}" if self.region else "global"
        return f"<Directory (id: {self.id}, name: {self.name}, {region})>"

    class Meta:
        #: The verbose name of the model
        verbose_name = _("media directory")
        #: The plural verbose name of the model
        verbose_name_plural = _("media directories")
        #: The fields which are used to sort the returned objects of a QuerySet
        ordering = ["-region", "name"]
