"""
This module contains view actions related to pages.
"""
import json
import logging
import os
import uuid

from mptt.exceptions import InvalidMove

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseNotFound, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404, get_list_or_404
from django.utils.text import slugify
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_POST

from backend.settings import WEBAPP_URL, XLIFF_UPLOAD_DIR
from xliff.utils import pages_to_zipped_xliffs, xliff_import_diff
from ...constants import text_directions
from ...decorators import region_permission_required, staff_required
from ...forms import PageForm
from ...models import Page, Language, Region, PageTranslation
from ...utils.file_utils import extract_zip_archive
from ...utils.pdf_utils import generate_pdf
from ...utils.slug_utils import generate_unique_slug

logger = logging.getLogger(__name__)


@require_POST
@login_required
@region_permission_required
def archive_page(request, page_id, region_slug, language_slug):
    """
    Archive page object

    :param request: The current request
    :type request: ~django.http.HttpResponse

    :param page_id: The id of the page which should be archived
    :type page_id: int

    :param region_slug: The slug of the current region
    :type region_slug: str

    :param language_slug: The slug of the current language
    :type language_slug: str

    :raises ~django.core.exceptions.PermissionDenied: If user does not have the permission to edit the specific page

    :return: A redirection to the :class:`~cms.views.pages.page_tree_view.PageTreeView`
    :rtype: ~django.http.HttpResponseRedirect
    """

    region = Region.get_current_region(request)
    page = get_object_or_404(region.pages, id=page_id)

    if not request.user.has_perm("cms.edit_page", page):
        raise PermissionDenied

    page.explicitly_archived = True
    page.save()

    logger.debug("%r archived by %r", page, request.user.profile)
    messages.success(request, _("Page was successfully archived"))

    return redirect(
        "pages",
        **{
            "region_slug": region_slug,
            "language_slug": language_slug,
        },
    )


@require_POST
@login_required
@region_permission_required
def restore_page(request, page_id, region_slug, language_slug):
    """
    Restore page object (set ``archived=False``)

    :param request: The current request
    :type request: ~django.http.HttpResponse

    :param page_id: The id of the page which should be restored
    :type page_id: int

    :param region_slug: The slug of the current region
    :type region_slug: str

    :param language_slug: The slug of the current language
    :type language_slug: str

    :raises ~django.core.exceptions.PermissionDenied: If user does not have the permission to edit the specific page

    :return: A redirection to the :class:`~cms.views.pages.page_tree_view.PageTreeView`
    :rtype: ~django.http.HttpResponseRedirect
    """

    region = Region.get_current_region(request)
    page = get_object_or_404(region.pages, id=page_id)

    if not request.user.has_perm("cms.edit_page", page):
        raise PermissionDenied

    page.explicitly_archived = False
    page.save()

    if page.implicitly_archived:
        logger.debug(
            "%r restored by %r but still implicitly archived",
            page,
            request.user.profile,
        )
        messages.info(
            request,
            _("Page was successfully restored.")
            + " "
            + _(
                "However, it is still archived because one of its parent pages is archived."
            ),
        )
        return redirect(
            "archived_pages",
            **{
                "region_slug": region_slug,
                "language_slug": language_slug,
            },
        )
    logger.debug("%r restored by %r", page, request.user.profile)
    messages.success(request, _("Page was successfully restored."))
    return redirect(
        "pages",
        **{
            "region_slug": region_slug,
            "language_slug": language_slug,
        },
    )


@login_required
@region_permission_required
@permission_required("cms.view_pages", raise_exception=True)
# pylint: disable=unused-argument
def view_page(request, page_id, region_slug, language_slug):
    """
    View page object

    :param request: The current request
    :type request: ~django.http.HttpResponse

    :param page_id: The id of the page which should be viewed
    :type page_id: int

    :param region_slug: The slug of the current region
    :type region_slug: str

    :param language_slug: The slug of the current language
    :type language_slug: str

    :return: A redirection to the :class:`~cms.views.pages.page_tree_view.PageTreeView`
    :rtype: ~django.http.HttpResponseRedirect
    """

    region = Region.get_current_region(request)
    page = get_object_or_404(region.pages, id=page_id)

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "pages/page_view.html"

    page_translation = page.get_translation(language_slug)
    mirrored_translation = page.get_mirrored_page_translation(language_slug)

    return render(
        request,
        template_name,
        {
            "page_translation": page_translation,
            "mirrored_translation": mirrored_translation,
            "mirrored_page_first": page.mirrored_page_first,
            "right_to_left": page_translation.language.text_direction
            == text_directions.RIGHT_TO_LEFT,
        },
    )


@require_POST
@login_required
@staff_required
def delete_page(request, page_id, region_slug, language_slug):
    """
    Delete page object

    :param request: The current request
    :type request: ~django.http.HttpResponse

    :param page_id: The id of the page which should be deleted
    :type page_id: int

    :param region_slug: The slug of the current region
    :type region_slug: str

    :param language_slug: The slug of the current language
    :type language_slug: str

    :return: A redirection to the :class:`~cms.views.pages.page_tree_view.PageTreeView`
    :rtype: ~django.http.HttpResponseRedirect
    """

    region = Region.get_current_region(request)
    page = get_object_or_404(region.pages, id=page_id)

    if page.children.exists():
        messages.error(request, _("You cannot delete a page which has subpages."))
    else:
        logger.info("%r deleted by %r", page, request.user.profile)
        page.delete()
        messages.success(request, _("Page was successfully deleted"))

    return redirect(
        "pages",
        **{
            "region_slug": region_slug,
            "language_slug": language_slug,
        },
    )


@login_required
@region_permission_required
# pylint: disable=unused-argument
def export_pdf(request, region_slug, language_slug):
    """
    Function for handling a pdf export request for pages.
    The pages get extracted from request.GET attribute and the request is forwarded to :func:`~cms.utils.pdf_utils.generate_pdf`

    :param request: Request submitted for rendering pdf document
    :type request: ~django.http.HttpRequest

    :param region_slug: unique region slug
    :type region_slug: str

    :param language_slug: bcp47 slug of the current language
    :type language_slug: str

    :raises ~django.core.exceptions.PermissionDenied: User login and permissions required

    :return: PDF document offered for download
    :rtype: ~django.http.HttpResponse
    """
    region = Region.get_current_region(request)
    # retrieve the selected page ids
    page_ids = request.POST.getlist("selected_ids[]")
    # collect the corresponding page objects
    pages = region.pages.filter(explicitly_archived=False, id__in=page_ids)
    # generate PDF document wrapped in a HtmlResponse object
    response = generate_pdf(region, language_slug, pages)
    if response.status_code == 200:
        # offer PDF document for download
        response["Content-Disposition"] = (
            response["Content-Disposition"] + "; attachment"
        )
    return response


def expand_page_translation_id(request, short_url_id):
    """
    Searches for a page translation with corresponding ID and redirects browser to web app

    :param request: The current request
    :type request: ~django.http.HttpRequest

    :param short_url_id: The id of the requested page
    :type short_url_id: int

    :return: A redirection to :class:`~backend.settings.WEBAPP_URL`
    :rtype: ~django.http.HttpResponseRedirect
    """

    page_translation = PageTranslation.objects.get(
        id=short_url_id
    ).latest_public_revision

    if page_translation and not page_translation.page.archived:
        return redirect(WEBAPP_URL + page_translation.get_absolute_url())
    return HttpResponseNotFound("<h1>Page not found</h1>")


@login_required
@region_permission_required
@permission_required("cms.view_pages", raise_exception=True)
def download_xliff(request, region_slug, language_slug):
    """
    Download a zip file of XLIFF files.
    The target languages and pages are selected and the source languages automatically determined.

    :param request: The current request
    :type request: ~django.http.HttpRequest

    :param region_slug: The slug of the current region
    :type region_slug: str

    :param language_slug: The slug of the target language
    :type language_slug: str

    :return: A redirection to the :class:`~cms.views.pages.page_tree_view.PageTreeView`
    :rtype: ~django.http.HttpResponseRedirect
    """

    page_ids = request.POST.getlist("selected_ids[]")

    if not page_ids:
        messages.error(
            request,
            _("No pages selected for XLIFF export."),
        )
        return redirect(
            "pages",
            **{
                "region_slug": region_slug,
                "language_slug": language_slug,
            },
        )

    region = Region.get_current_region(request)
    pages = get_list_or_404(region.pages, id__in=page_ids)

    target_language = get_object_or_404(
        region.language_tree_nodes,
        language__slug=language_slug,
        parent__isnull=False,
    ).language

    zip_url = pages_to_zipped_xliffs(pages, target_language)

    logger.info(
        "XLIFFS for pages %r exported by %r",
        page_ids,
        request.user.profile,
    )
    PageTranslation.objects.filter(page__in=pages, language=target_language).update(
        currently_in_translation=True
    )
    request.session["xliff-download-url"] = zip_url
    return redirect(
        "pages",
        **{
            "region_slug": region_slug,
            "language_slug": language_slug,
        },
    )


@require_POST
@login_required
# pylint: disable=unused-argument
def post_translation_state_ajax(request, region_slug):
    """This view is called for manually unseting the translation process

    :param request: ajax request
    :type request: ~django.http.HttpRequest
    :param region_slug: The slug of the current region
    :type region_slug: str
    :return: on success returns language of updated translation
    :rtype: ~django.http.JsonResponse
    """
    decoded_json = json.loads(request.body.decode("utf-8"))
    target_language = decoded_json["language"]
    page_id = decoded_json["pageId"]
    translation_state = decoded_json["translationState"]
    region = Region.get_current_region(request)
    page = get_object_or_404(region.pages, id=page_id)
    page_translation = page.get_translation(target_language.code)
    if page_translation:
        page_translation.update(currently_in_translation=translation_state)
        return JsonResponse({"language": target_language})
    return JsonResponse(
        {"error": _("Could not update page translation state")}, status=400
    )


@require_POST
@login_required
@region_permission_required
@permission_required("cms.edit_pages", raise_exception=True)
def upload_xliff(request, region_slug, language_slug):
    """
    Upload and import an XLIFF file

    :param request: The current request
    :type request: ~django.http.HttpResponse

    :param region_slug: The slug of the current region
    :type region_slug: str

    :param language_slug: The slug of the current language
    :type language_slug: str

    :return: A redirection to the :class:`~cms.views.pages.page_tree_view.PageTreeView`
    :rtype: ~django.http.HttpResponseRedirect
    """
    xliff_paths = []
    upload_files = request.FILES.getlist("xliff_file")
    if upload_files:
        logger.debug("Uploaded files: %r", upload_files)
        upload_dir = os.path.join(XLIFF_UPLOAD_DIR, str(uuid.uuid4()))
        os.makedirs(upload_dir, exist_ok=True)
        for upload_file in upload_files:
            if not upload_file.name.endswith((".zip", ".xliff", ".xlf")):
                # File type not supported
                messages.error(
                    request,
                    _('File "{}" is neither a ZIP archive nor an XLIFF file.').format(
                        upload_file.name
                    ),
                )
                logger.warning(
                    "File %r is neither a ZIP archive nor an XLIFF file",
                    upload_file.name,
                )
                continue

            with open(os.path.join(upload_dir, upload_file.name), "wb+") as file_write:
                # Using chunks() instead of read() ensures that large files don’t overwhelm your system’s memory
                for chunk in upload_file.chunks():
                    file_write.write(chunk)

            if upload_file.name.endswith(".zip"):
                # Extract zip archive
                xliff_paths_tmp, invalid_file_paths = extract_zip_archive(
                    os.path.join(upload_dir, upload_file.name), upload_dir
                )
                # Append contents of zip archive to total list of xliff files
                xliff_paths += xliff_paths_tmp
                if not xliff_paths_tmp:
                    messages.error(
                        request,
                        _('The ZIP archive "{}" does not contain XLIFF files.').format(
                            upload_file.name
                        ),
                    )
                elif invalid_file_paths:
                    messages.warning(
                        request,
                        _(
                            'The ZIP archive "{}" contains the following invalid files: "{}"'
                        ).format(upload_file.name, '", "'.join(invalid_file_paths)),
                    )
            else:
                xliff_paths.append(os.path.join(upload_dir, upload_file.name))
    else:
        messages.error(
            request,
            _("No XLIFF file was selected for import."),
        )

    if xliff_paths and upload_dir:
        logger.debug("Uploaded XLIFF files: %r", xliff_paths)
        # Remove duplicates
        xliff_paths = list(dict.fromkeys(xliff_paths))
        # logger.debug("Translation diff: %r", diff)
        return render(
            request,
            "pages/page_xliff_confirm.html",
            {
                "upload_dir": os.path.basename(upload_dir),
                "translation_diffs": xliff_import_diff(upload_dir),
                "language": Language.objects.get(slug=language_slug),
            },
        )
    return redirect(
        "pages",
        **{
            "region_slug": region_slug,
            "language_slug": language_slug,
        },
    )


@require_POST
@login_required
@region_permission_required
@permission_required("cms.edit_pages", raise_exception=True)
def confirm_xliff_import(request, region_slug, language_slug):
    """
    Confirm a started XLIFF import

    :param request: The current request
    :type request: ~django.http.HttpResponse

    :param region_slug: The slug of the current region
    :type region_slug: str

    :param language_slug: The slug of the current language
    :type language_slug: str

    :return: A redirection to the :class:`~cms.views.pages.page_tree_view.PageTreeView`
    :rtype: ~django.http.HttpResponseRedirect
    """

    if request.POST.get("upload_dir"):
        upload_dir = os.path.join(XLIFF_UPLOAD_DIR, request.POST.get("upload_dir"))
        # pylint: disable=unused-variable
        xliff_paths = [
            os.path.join(upload_dir, f)
            for f in os.listdir(upload_dir)
            if os.path.isfile(os.path.join(upload_dir, f))
            and f.endswith((".xliff", ".xlf"))
        ]
        # Todo: import XLIFF files
        logger.info(
            "XLIFFS of directory %r imported by %r",
            upload_dir,
            request.user.profile,
        )
    return redirect(
        "pages",
        **{
            "region_slug": region_slug,
            "language_slug": language_slug,
        },
    )


@require_POST
@login_required
@region_permission_required
@permission_required("cms.edit_pages", raise_exception=True)
# pylint: disable=too-many-arguments
def move_page(request, region_slug, language_slug, page_id, target_id, position):
    """
    Move a page object in the page tree

    :param request: The current request
    :type request: ~django.http.HttpResponse

    :param region_slug: The slug of the current region
    :type region_slug: str

    :param language_slug: The slug of the current language
    :type language_slug: str

    :param page_id: The id of the page which should be moved
    :type page_id: int

    :param target_id: The id of the page which determines the new position
    :type target_id: int

    :param position: The new position of the page relative to the target (choices: :mod:`cms.constants.position`)
    :type position: str

    :return: A redirection to the :class:`~cms.views.pages.page_tree_view.PageTreeView`
    :rtype: ~django.http.HttpResponseRedirect
    """

    region = Region.get_current_region(request)
    page = get_object_or_404(region.pages, id=page_id)
    target = get_object_or_404(region.pages, id=target_id)

    try:
        page.move_to(target, position)
        logger.debug(
            "%r moved to %r of %r by %r",
            page,
            position,
            target,
            request.user.profile,
        )
        messages.success(
            request,
            _('The page "{page}" was successfully moved.').format(
                page=page.best_translation.title
            ),
        )
    except (ValueError, InvalidMove) as e:
        messages.error(request, e)
        logger.exception(e)

    return redirect(
        "pages",
        **{
            "region_slug": region_slug,
            "language_slug": language_slug,
        },
    )


@require_POST
@login_required
@region_permission_required
@permission_required("cms.edit_pages", raise_exception=True)
@permission_required("cms.grant_page_permissions", raise_exception=True)
# pylint: disable=too-many-branches
def grant_page_permission_ajax(request):
    """
    Grant a user editing or publishing permissions on a specific page object

    :param request: The current request
    :type request: ~django.http.HttpResponse

    :raises ~django.core.exceptions.PermissionDenied: If page permissions are disabled for this region or the user does
                                                      not have the permission to grant page permissions

    :return: The rendered page permission table
    :rtype: ~django.template.response.TemplateResponse
    """

    try:
        data = json.loads(request.body.decode("utf-8"))
        permission = data.get("permission")
        page = Page.objects.get(id=data.get("page_id"))
        user = get_user_model().objects.get(id=data.get("user_id"))

        logger.debug(
            "[AJAX] %r wants to grant %r the permission to %s %r",
            request.user.profile,
            user.profile,
            permission,
            page,
        )

        if not page.region.page_permissions_enabled:
            logger.warning(
                "Error: Page permissions are not activated for %r",
                page.region,
            )
            raise PermissionDenied

        if not request.user.has_perm("cms.grant_page_permissions"):
            logger.warning(
                "Error: %r does not have the permission to grant page permissions",
                request.user.profile,
            )
            raise PermissionDenied

        if not (request.user.is_superuser or request.user.is_staff):
            # additional checks if requesting user is no superuser or staff
            if page.region not in request.user.profile.regions:
                # requesting user can only grant permissions for pages of his region
                logger.warning(
                    "Error: %r cannot grant permissions for %r",
                    request.user.profile,
                    page.region,
                )
                raise PermissionDenied
            if page.region not in user.profile.regions:
                # user can only receive permissions for pages of his region
                logger.warning(
                    "Error: %r cannot receive permissions for %r",
                    user.profile,
                    page.region,
                )
                raise PermissionDenied

        if permission == "edit":
            # check, if the user already has this permission
            if user.has_perm("cms.edit_page", page):
                message = _(
                    "Information: The user {user} has this permission already."
                ).format(user=user.username)
                level_tag = "info"
            else:
                # else grant the permission by adding the user to the editors of the page
                page.editors.add(user)
                page.save()
                message = _("Success: The user {user} can now edit this page.").format(
                    user=user.username
                )
                level_tag = "success"
        elif permission == "publish":
            # check, if the user already has this permission
            if user.has_perm("cms.publish_page", page):
                message = _(
                    "Information: The user {user} has this permission already."
                ).format(user=user.username)
                level_tag = "info"
            else:
                # else grant the permission by adding the user to the publishers of the page
                page.publishers.add(user)
                page.save()
                message = _(
                    "Success: The user {user} can now publish this page."
                ).format(user=user.username)
                level_tag = "success"
        else:
            logger.warning("Error: The permission %r is not supported", permission)
            raise PermissionDenied
    # pylint: disable=broad-except
    except Exception as e:
        logger.exception(e)
        message = _("An error has occurred. Please contact an administrator.")
        level_tag = "error"

    logger.debug(message)

    return render(
        request,
        "pages/_page_permission_table.html",
        {
            "page": page,
            "page_form": PageForm(instance=page, region=page.region),
            "permission_message": {"message": message, "level_tag": level_tag},
        },
    )


@require_POST
@login_required
@region_permission_required
@permission_required("cms.edit_pages", raise_exception=True)
@permission_required("cms.grant_page_permissions", raise_exception=True)
# pylint: disable=too-many-branches
def revoke_page_permission_ajax(request):
    """
    Remove a page permission for a given user and page

    :param request: The current request
    :type request: ~django.http.HttpResponse

    :raises ~django.core.exceptions.PermissionDenied: If page permissions are disabled for this region or the user does
                                                      not have the permission to revoke page permissions

    :return: The rendered page permission table
    :rtype: ~django.template.response.TemplateResponse
    """

    try:
        data = json.loads(request.body.decode("utf-8"))
        permission = data.get("permission")
        page = Page.objects.get(id=data.get("page_id"))
        user = get_user_model().objects.get(id=data.get("user_id"))

        logger.debug(
            "[AJAX] %r wants to revoke the permission to %s %r from %r",
            request.user.profile,
            permission,
            page,
            user.profile,
        )

        if not page.region.page_permissions_enabled:
            logger.warning(
                "Error: Page permissions are not activated for %r",
                page.region,
            )
            raise PermissionDenied

        if not request.user.has_perm("cms.grant_page_permissions"):
            logger.warning(
                "Error: %r does not have the permission to revoke page permissions",
                request.user.profile,
            )
            raise PermissionDenied

        if not (request.user.is_superuser or request.user.is_staff):
            # additional checks if requesting user is no superuser or staff
            if page.region not in request.user.profile.regions:
                # requesting user can only revoke permissions for pages of his region
                logger.warning(
                    "Error: %r cannot revoke permissions for %r",
                    request.user.profile,
                    page.region,
                )
                raise PermissionDenied

        if permission == "edit":
            if user in page.editors.all():
                # revoke the permission by removing the user to the editors of the page
                page.editors.remove(user)
                page.save()
            # check, if the user has this permission anyway
            if user.has_perm("cms.edit_page", page):
                message = _(
                    "Information: The user {user} has been removed from the editors of this page, "
                    "but has the implicit permission to edit this page anyway."
                ).format(user=user.username)
                level_tag = "info"
            else:
                message = _(
                    "Success: The user {user} cannot edit this page anymore."
                ).format(user=user.username)
                level_tag = "success"
        elif permission == "publish":
            if user in page.publishers.all():
                # revoke the permission by removing the user to the publishers of the page
                page.publishers.remove(user)
                page.save()
            # check, if the user already has this permission
            if user.has_perm("cms.publish_page", page):
                message = _(
                    "Information: The user {user} has been removed from the publishers of this page, "
                    "but has the implicit permission to publish this page anyway."
                ).format(user=user.username)
                level_tag = "info"
            else:
                message = _(
                    "Success: The user {user} cannot publish this page anymore."
                ).format(user=user.username)
                level_tag = "success"
        else:
            logger.warning("Error: The permission %r is not supported", permission)
            raise PermissionDenied
    # pylint: disable=broad-except
    except Exception as e:
        logger.exception(e)
        message = _("An error has occurred. Please contact an administrator.")
        level_tag = "error"

    logger.debug(message)

    return render(
        request,
        "pages/_page_permission_table.html",
        {
            "page": page,
            "page_form": PageForm(instance=page, region=page.region),
            "permission_message": {"message": message, "level_tag": level_tag},
        },
    )


@login_required
@region_permission_required
@permission_required("cms.edit_pages", raise_exception=True)
# pylint: disable=unused-argument
def get_page_order_table_ajax(request, region_slug, page_id, parent_id):
    """
    Retrieve the order table for a given page and a given parent page.
    This is used in the page form to change the order of a page relative to its siblings.

    :param request: The current request
    :type request: ~django.http.HttpResponse

    :param region_slug: The slug of the current region
    :type region_slug: str

    :param page_id: The id of the page of the current page form
    :type page_id: int

    :param parent_id: The id of the parent page to which the order table should be returned
    :type parent_id: int

    :return: The rendered page order table
    :rtype: ~django.template.response.TemplateResponse
    """

    region = Region.get_current_region(request)
    page = get_object_or_404(region.pages, id=page_id)

    if parent_id == "0":
        siblings = region.pages.filter(level=0)
    else:
        siblings = region.pages.filter(parent__id=parent_id)

    logger.debug(
        "Page order table for %r and siblings %r",
        page,
        siblings,
    )

    return render(
        request,
        "pages/_page_order_table.html",
        {
            "page": page,
            "siblings": siblings,
        },
    )


@login_required
@region_permission_required
@permission_required("cms.edit_pages", raise_exception=True)
# pylint: disable=unused-argument
def get_new_page_order_table_ajax(request, region_slug, parent_id):
    """
    Retrieve the order table for a new page and a given parent page.
    This is used in the page form to set the position of a new page relative to its siblings.

    :param request: The current request
    :type request: ~django.http.HttpResponse

    :param region_slug: The slug of the current region
    :type region_slug: str

    :param parent_id: The id of the parent page to which the order table should be returned
    :type parent_id: int

    :return: The rendered page order table
    :rtype: ~django.template.response.TemplateResponse
    """

    region = Region.get_current_region(request)

    if parent_id == "0":
        siblings = region.pages.filter(level=0)
    else:
        siblings = region.pages.filter(parent__id=parent_id)

    logger.debug(
        "Page order table for a new page and siblings %r",
        siblings,
    )

    return render(
        request,
        "pages/_page_order_table.html",
        {
            "siblings": siblings,
        },
    )


@login_required
def render_mirrored_page_field(request):
    """
    Retrieve the rendered mirrored page field template

    :param request: The current request
    :type request: ~django.http.HttpResponse

    :return: The rendered mirrored page field
    :rtype: ~django.template.response.TemplateResponse
    """
    # Get the region from which the content should be embedded
    region = get_object_or_404(Region, id=request.GET.get("region_id"))
    # Get the page in which the content should be embedded (to exclude it from the possible selections)
    page = Page.objects.filter(id=request.GET.get("page_id")).first()
    page_form = PageForm(
        {"mirrored_page_region": region.id},
        instance=page,
        region=region,
    )
    return render(
        request,
        "pages/_mirrored_page_field.html",
        {
            "page_form": page_form,
        },
    )


@login_required
@region_permission_required
@permission_required("cms.edit_pages", raise_exception=True)
# pylint: disable=unused-argument
def slugify_ajax(request, region_slug, language_slug):
    """checks the current user input for page title and generates unique slug for permalink

    :param request: The current request
    :type request: ~django.http.HttpResponse
    :param region_slug: region identifier
    :type region_slug: str
    :param language_slug: language slug
    :type language_slug: str
    :return: unique page translation slug
    :rtype: str
    """
    json_data = json.loads(request.body)
    form_title = slugify(json_data["title"], allow_unicode=True)
    region = Region.get_current_region(request)
    language = get_object_or_404(region.languages, slug=language_slug)
    page = region.pages.filter(id=request.GET.get("page")).first()
    page_translation = PageTranslation.objects.filter(
        page=page,
        language=language,
    ).first()
    kwargs = {
        "slug": form_title,
        "manager": PageTranslation.objects,
        "object_instance": page_translation,
        "foreign_model": "page",
        "region": region,
        "language": language,
    }
    unique_slug = generate_unique_slug(**kwargs)
    return JsonResponse({"unique_slug": unique_slug})
