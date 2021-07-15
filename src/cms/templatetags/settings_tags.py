"""
This contains tags for accessing settings
"""
from django import template

from backend.settings import WEBAPP_URL


register = template.Library()


@register.simple_tag
def get_webapp_url():
    """
    This tag returns the ``WEBAPP_URL``

    :return: The url of the current web application
    :rtype: str
    """
    return WEBAPP_URL
