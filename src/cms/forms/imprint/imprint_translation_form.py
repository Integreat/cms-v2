import logging

from ...constants import status
from ...models import ImprintPageTranslation
from ..custom_content_model_form import CustomContentModelForm


logger = logging.getLogger(__name__)


class ImprintTranslationForm(CustomContentModelForm):
    """
    Form for creating and modifying imprint translation objects
    """

    class Meta:
        model = ImprintPageTranslation
        fields = ["title", "status", "text", "minor_edit"]

    def __init__(self, **kwargs):
        """
        Initialize Imprint page translation form

        :param kwargs: The supplied keyword arguments
        :type kwargs: dict
        """

        # To set the status value through the submit button, we have to overwrite the field value for status.
        # We could also do this in the save() function, but this would mean that it is not recognized in changed_data.
        # Check if POST data was submitted
        if "data" in kwargs:
            # Copy QueryDict because it is immutable
            data = kwargs.pop("data").copy()
            # Update the POST field with the status corresponding to the submitted button
            if "submit_auto" in data:
                data["status"] = status.AUTO_SAVE
            elif "submit_draft" in data:
                data["status"] = status.DRAFT
            elif "submit_public" in data:
                data["status"] = status.PUBLIC
            # Set the kwargs to updated POST data again
            kwargs["data"] = data
            logger.debug(
                "Changed POST data 'status' manually to %r", data.get("status")
            )

        super().__init__(**kwargs)

    def save(self, commit=True):
        """
        This method extends the default ``save()``-method of the base :class:`~django.forms.ModelForm` to set attributes
        which are not directly determined by input fields.

        :param commit: Whether or not the changes should be written to the database
        :type commit: bool

        :return: The saved imprint page translation object
        :rtype: ~cms.models.pages.imprint_page_translation.ImprintPageTranslation
        """

        # Create new version if content changed
        if not {"slug", "title", "text"}.isdisjoint(self.changed_data):
            self.instance.version += 1
            self.instance.pk = None

        # Save CustomModelForm
        return super().save(commit=commit)

    def clean_text(self):
        """
        Validate the text field (see :ref:`overriding-modelform-clean-method`)

        :raises ~django.core.exceptions.ValidationError: When a heading 1 (``<h1>``) is used in the text content and applies changes to <img>- and <a>-Tags to match the guidelines.

        :return: The valid text
        :rtype: str
        """
        return self.content_clean_method("text")
