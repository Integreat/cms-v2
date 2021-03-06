import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView

from ...constants import status
from ...decorators import region_permission_required, permission_required
from ...models import Region, Language, ImprintPage

logger = logging.getLogger(__name__)


@method_decorator(login_required, name="dispatch")
@method_decorator(region_permission_required, name="dispatch")
@method_decorator(permission_required("cms.view_imprintpage"), name="dispatch")
@method_decorator(permission_required("cms.change_imprintpage"), name="post")
class ImprintRevisionView(TemplateView):
    """
    View for browsing the imprint revisions and restoring old imprint revisions
    """

    template_name = "imprint/imprint_revisions.html"
    base_context = {"current_menu_item": "imprint"}

    def get(self, request, *args, **kwargs):
        """
        Render imprint page revision slider

        :param request: The current request
        :type request: ~django.http.HttpResponse

        :param args: The supplied arguments
        :type args: list

        :param kwargs: The supplied keyword arguments
        :type kwargs: dict

        :raises ~django.http.Http404: If no imprint exists for the region

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """

        region = Region.get_current_region(request)
        try:
            imprint = region.imprint
        except ImprintPage.DoesNotExist as e:
            raise Http404 from e

        language = get_object_or_404(
            region.language_tree_nodes, language__slug=kwargs.get("language_slug")
        ).language

        imprint_translations = imprint.translations.filter(language=language)

        if not imprint_translations.exists():
            return redirect(
                "edit_imprint",
                **{
                    "region_slug": region.slug,
                    "language_slug": language.slug,
                }
            )

        selected_revision = imprint_translations.filter(
            version=kwargs.get("selected_revision", imprint_translations.count())
        )

        if not selected_revision.exists():
            messages.error(request, _("This revision does not exist."))
            return redirect(
                "imprint_revisions",
                **{
                    "region_slug": region.slug,
                    "language_slug": language.slug,
                }
            )

        if imprint.archived:
            messages.warning(
                request,
                _(
                    "You cannot restore revisions of this imprint because it is archived."
                ),
            )

        return render(
            request,
            self.template_name,
            {
                **self.base_context,
                "imprint": imprint,
                "imprint_translations": imprint_translations,
                "api_revision": imprint_translations.filter(
                    status=status.PUBLIC
                ).first(),
                "selected_revision": selected_revision.first(),
                "language": language,
            },
        )

    # pylint: disable=unused-argument
    def post(self, request, *args, **kwargs):
        """
        Restore a previous revision of an imprint page translation

        :param request: The current request
        :type request: ~django.http.HttpResponse

        :param args: The supplied arguments
        :type args: list

        :param kwargs: The supplied keyword arguments
        :type kwargs: dict

        :raises ~django.http.Http404: If no imprint exists for the region

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """

        region = Region.get_current_region(request)
        try:
            imprint = region.imprint
        except ImprintPage.DoesNotExist as e:
            raise Http404 from e

        language = Language.objects.get(slug=kwargs.get("language_slug"))

        revision = imprint.translations.filter(
            language=language, version=request.POST.get("revision")
        ).first()

        if not revision:
            messages.error(request, _("This revision does not exist."))
            return redirect(
                "imprint_revisions",
                **{
                    "region_slug": region.slug,
                    "language_slug": language.slug,
                }
            )

        current_revision = imprint.get_translation(language.slug)

        if (
            revision.title == current_revision.title
            and revision.text == current_revision.text
        ):
            messages.error(
                request,
                _(
                    "This revision is identical to the current version of this translation."
                ),
            )
            return redirect(
                "imprint_revisions",
                **{
                    "region_slug": region.slug,
                    "language_slug": language.slug,
                }
            )

        revision.pk = None
        revision.version = current_revision.version + 1

        if request.POST.get("submit_draft"):
            revision.status = status.DRAFT
        elif request.POST.get("submit_review"):
            revision.status = status.REVIEW
        elif request.POST.get("submit_public"):
            revision.status = status.PUBLIC

        revision.save()

        messages.success(request, _("The revision was successfully restored"))

        imprint_translations = imprint.translations.filter(language=language)

        return render(
            request,
            self.template_name,
            {
                **self.base_context,
                "imprint": imprint,
                "imprint_translations": imprint_translations,
                "api_revision": imprint_translations.filter(
                    status=status.PUBLIC
                ).first(),
                "selected_revision": revision,
                "language": language,
            },
        )
