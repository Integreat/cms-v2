import re
import logging
import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from backend.settings import WEBAPP_URL
from ...decorators import region_permission_required
from ...models.regions.region import Region

logger = logging.getLogger(__name__)

# The maximum number of results returned by `search_content_ajax`
MAX_RESULT_COUNT = 20


def format_object_translation(object_translation, typ):
    """
    Formats the [poi/event/page]-translation as json

    :param object_translation: A translation object which has a title and a permalink
    :type object_translation: ~cms.models.events.event.Event or ~cms.models.pages.page.Page or ~cms.models.pois.poi.POI
    :param typ: The type of this object
    :type typ: str
    :return: A dictionary with the title, url and type of the translation object
    :rtype: dict
    """
    return {
        "title": object_translation.title,
        "url": f"{WEBAPP_URL}/{object_translation.permalink}",
        "type": typ,
    }


def find_objects(object_manager, query, language_slug):
    """
    Filters all object translations from ``object_manager`` of this language
    that match ``query`` and returns them and their ranking

    :param object_manager: The manager for a specific model
    :type object_manager: ~django.db.models.Manager
    :param query: The query string used for filtering the objects
    :type query: str
    :param language_slug: The language slug
    :type language_slug: str
    :return: an iterator over all objects that match query and their search priority
    :rtype: Iterator[:class:`tuple`]
    """
    for obj in object_manager.all():
        if obj.archived:
            continue
        object_translation = obj.get_public_translation(language_slug)
        if not object_translation:
            continue

        title = object_translation.title
        slug = object_translation.slug

        if re.search(query, title, re.IGNORECASE):
            yield (2, object_translation)
        elif re.search(query, slug, re.IGNORECASE):
            yield (2, object_translation)


@require_POST
@login_required
@region_permission_required
# pylint: disable=unused-argument
def search_content_ajax(request, region_slug, language_slug):
    """Searches all pois, events and pages for the current region and returns all that
    match the search query. Results which match the query in the title or slug get ranked
    higher than results which only match through their text content.

    :param request: The current request
    :type request: ~django.http.HttpResponse
    :param region_slug: region identifier
    :type region_slug: str
    :param language_slug: language slug
    :type language_slug: str
    :return: Json object containing all matching elements, of shape {title: str, url: str, type: str}
    :rtype: ~django.http.JsonResponse
    """

    region = Region.get_current_region(request)
    raw_query = json.loads(request.body.decode("utf-8"))["query_string"]
    query = re.escape(raw_query)

    logger.debug(
        'Ajax call: Live search for pois, events and pages with query "%r"', raw_query
    )

    results = []

    user = request.user
    if user.has_perm("cms.view_event"):
        results.extend(
            (prio, format_object_translation(obj, "event"))
            for (prio, obj) in find_objects(region.events, query, language_slug)
        )

    if user.has_perm("cms.view_page"):
        results.extend(
            (prio, format_object_translation(obj, "page"))
            for (prio, obj) in find_objects(region.pages, query, language_slug)
        )

    if user.has_perm("cms.view_poi"):
        results.extend(
            (prio, format_object_translation(obj, "poi"))
            for (prio, obj) in find_objects(region.pois, query, language_slug)
        )

    # sort first by highest priority and then alphabetically by title
    results.sort(key=lambda res: (-res[0], res[1]["title"]))

    return JsonResponse({"data": [i[1] for i in results[:MAX_RESULT_COUNT]]})
