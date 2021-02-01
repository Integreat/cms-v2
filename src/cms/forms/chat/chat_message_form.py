import logging

from django import forms

from ...models import ChatMessage

logger = logging.getLogger(__name__)


class ChatMessageForm(forms.ModelForm):
    """
    Form for submitting chat messages
    """

    class Meta:
        """
        This class contains additional meta configuration of the form class, see the :class:`django.forms.ModelForm`
        for more information.
        """

        model = ChatMessage
        fields = ["text"]

    def __init__(self, *args, **kwargs):
        """
        Initialize chat message form

        :param args: The supplied arguments
        :type args: list

        :param kwargs: The supplied keyword arguments
        :type kwargs: dict
        """

        logger.info(
            "New ChatMessageForm instantiated with args %s and kwargs %s", args, kwargs
        )

        # pop kwarg to make sure the super class does not get this param
        sender = kwargs.pop("sender", None)

        super().__init__(*args, **kwargs)

        self.instance.sender = sender