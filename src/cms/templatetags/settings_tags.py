"""
This contains tags for accessing settings
"""
from django import template

from backend.settings import BASE_URL, WEBAPP_URL


register = template.Library()


@register.simple_tag
def get_webapp_url():
    """
    This tag returns the ``WEBAPP_URL``

    :return: The url of the current web application
    :rtype: str
    """
    return WEBAPP_URL


@register.simple_tag
def get_base_url():
    """
    This tag returns the ``BASE_URL``

    :return: The base url of the current web application
    :rtype: str
    """
    return BASE_URL
