import logging

from datetime import time

from django import forms
from django.utils.translation import ugettext_lazy as _

from ...models import Event
from ..custom_model_form import CustomModelForm
from ..icon_widget import IconWidget

logger = logging.getLogger(__name__)


class EventForm(CustomModelForm):
    """
    Form for creating and modifying event objects
    """

    # Whether or not the event is all day
    is_all_day = forms.BooleanField(required=False, label=_("All-day"))
    # Whether or not the event is recurring
    is_recurring = forms.BooleanField(
        required=False,
        label=_("Recurring"),
        help_text=_("Determines whether the event is repeated at regular intervals."),
    )
    # Whether or not the event has a physical location
    has_physical_location = forms.BooleanField(
        required=False,
        label=_("Event does not have a physical location"),
        label_suffix='',
    )

    class Meta:
        """
        This class contains additional meta configuration of the form class, see the :class:`django.forms.ModelForm`
        for more information.
        """

        #: The model of this :class:`django.forms.ModelForm`
        model = Event
        #: The fields of the model which should be handled by this form
        fields = [
            "start_date",
            "start_time",
            "end_date",
            "end_time",
            "icon",
            "location",
        ]
        #: The widgets which are used in this form
        widgets = {
            "start_date": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
            "end_date": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
            "start_time": forms.TimeInput(format="%H:%M", attrs={"type": "time"}),
            "end_time": forms.TimeInput(format="%H:%M", attrs={"type": "time"}),
            "icon": IconWidget(),
        }

    def __init__(self, **kwargs):
        """
        Initialize event form

        :param kwargs: The supplied keyword arguments
        :type kwargs: dict
        """

        # Instantiate CustomModelForm
        super().__init__(**kwargs)

        if self.instance.id:
            # Initialize BooleanFields based on Event properties
            self.fields["is_all_day"].initial = self.instance.is_all_day
            self.fields["is_recurring"].initial = self.instance.is_recurring

    def clean(self):
        """
        Validate form fields which depend on each other, see :meth:`django.forms.Form.clean`

        :return: The cleaned form data
        :rtype: dict
        """
        cleaned_data = super().clean()

        # make self.data mutable to allow values to be changed manually
        self.data = self.data.copy()

        if cleaned_data.get("is_all_day"):
            cleaned_data["start_time"] = time.min
            self.data["start_time"] = time.min
            # Strip seconds and microseconds because our time fields only has hours and minutes
            cleaned_data["end_time"] = time.max.replace(second=0, microsecond=0)
            self.data["end_time"] = time.max.replace(second=0, microsecond=0)
        else:
            # If at least one of the time fields are missing, show an error
            if not cleaned_data.get("start_time"):
                self.add_error(
                    "start_time",
                    forms.ValidationError(
                        _("If the event is not all-day, the start time is required"),
                        code="required",
                    ),
                )
            if not cleaned_data.get("end_time"):
                self.add_error(
                    "end_time",
                    forms.ValidationError(
                        _("If the event is not all-day, the end time is required"),
                        code="required",
                    ),
                )
            elif cleaned_data["start_time"] == time.min and cleaned_data[
                "end_time"
            ] == time.max.replace(second=0, microsecond=0):
                self.data["is_all_day"] = True

        if cleaned_data.get("end_date") and cleaned_data.get("start_date"):
            if cleaned_data.get("end_date") < cleaned_data.get("start_date"):
                # If both dates are given, check if they are valid
                self.add_error(
                    "end_date",
                    forms.ValidationError(
                        _(
                            "The end of the event can't be before the start of the event"
                        ),
                        code="invalid",
                    ),
                )
            elif cleaned_data.get("end_date") == cleaned_data.get("start_date"):
                # If both dates are identical, check the times
                if cleaned_data.get("end_time") and cleaned_data.get("start_time"):
                    # If both times are given, check if they are valid
                    if cleaned_data.get("end_time") < cleaned_data.get("start_time"):
                        self.add_error(
                            "end_time",
                            forms.ValidationError(
                                _(
                                    "The end of the event can't be before the start of the event"
                                ),
                                code="invalid",
                            ),
                        )

        logger.debug("EventForm validated [2] with cleaned data %r", cleaned_data)
        return cleaned_data
