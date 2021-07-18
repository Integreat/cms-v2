import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView

from backend.settings import IMPRINT_SLUG, WEBAPP_URL
from ...decorators import region_permission_required, permission_required
from ...forms import ImprintTranslationForm
from ...models import ImprintPageTranslation, ImprintPage, Region

logger = logging.getLogger(__name__)


@method_decorator(login_required, name="dispatch")
@method_decorator(region_permission_required, name="dispatch")
@method_decorator(permission_required("cms.view_imprintpage"), name="dispatch")
@method_decorator(permission_required("cms.change_imprintpage"), name="post")
class ImprintView(TemplateView):
    """
    View for the imprint page form and imprint page translation form
    """

    template_name = "imprint/imprint_form.html"
    base_context = {
        "current_menu_item": "imprint",
        "WEBAPP_URL": WEBAPP_URL,
        "IMPRINT_SLUG": IMPRINT_SLUG,
    }

    def get(self, request, *args, **kwargs):
        """
        Render :class:`~cms.forms.imprint.imprint_translation_form.ImprintTranslationForm`

        :param request: The current request
        :type request: ~django.http.HttpResponse

        :param args: The supplied arguments
        :type args: list

        :param kwargs: The supplied keyword arguments
        :type kwargs: dict

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """

        # current region
        region = Region.get_current_region(request)

        # current language
        language_slug = kwargs.get("language_slug")
        if language_slug:
            language = get_object_or_404(region.languages, slug=language_slug)
        elif region.default_language:
            return redirect(
                "edit_imprint",
                **{
                    "region_slug": region.slug,
                    "language_slug": region.default_language.slug,
                },
            )
        else:
            messages.error(
                request,
                _("Please create at least one language node before creating pages."),
            )
            return redirect(
                "language_tree",
                **{
                    "region_slug": region.slug,
                },
            )

        # get imprint and translation objects if they exist
        try:
            imprint = region.imprint
        except ImprintPage.DoesNotExist:
            imprint = None

        imprint_translation = ImprintPageTranslation.objects.filter(
            page=imprint,
            language=language,
        ).first()

        disabled = False
        if imprint:
            # Make form disabled if imprint is archived
            if imprint.archived:
                disabled = True
                messages.warning(
                    request, _("You cannot manage the imprint because it is archived.")
                )
            # Show information if latest changes are only saved as draft
            public_translation = imprint.get_public_translation(language.slug)
            if public_translation and imprint_translation != public_translation:
                messages.info(
                    request,
                    _(
                        "This is <b>not</b> the most recent public revision of this translation. Instead, <a href='%(revision_url)s' class='underline hover:no-underline'>revision %(revision)s</a> is shown in the apps."
                    )
                    % {
                        "revision_url": reverse(
                            "imprint_revisions",
                            kwargs={
                                "region_slug": region.slug,
                                "language_slug": language.slug,
                                "selected_revision": public_translation.version,
                            },
                        ),
                        "revision": public_translation.version,
                    },
                )

        # Make form disabled if user has no permission to manage the imprint
        if not request.user.has_perm("cms.change_imprintpage"):
            disabled = True
            messages.warning(
                request, _("You don't have the permission to edit the imprint.")
            )

        imprint_translation_form = ImprintTranslationForm(
            instance=imprint_translation, disabled=disabled
        )

        # Pass side by side language options
        side_by_side_language_options = self.get_side_by_side_language_options(
            region, language, imprint
        )

        return render(
            request,
            self.template_name,
            {
                **self.base_context,
                "imprint_translation_form": imprint_translation_form,
                "imprint": imprint,
                "language": language,
                # Languages for tab view
                "languages": region.languages if imprint else [language],
                "side_by_side_language_options": side_by_side_language_options,
            },
        )

    # pylint: disable=too-many-branches,unused-argument
    def post(self, request, *args, **kwargs):
        """
        Binds the user input data to the imprint form and validates the input.
        Forms containing images/files need to be additionally instantiated with the FILES attribute of request objects,
        see :doc:`django:topics/http/file-uploads`

        :param request: Request submitted for saving imprint form
        :type request: ~django.http.HttpRequest

        :param args: The supplied arguments
        :type args: list

        :param kwargs: The supplied keyword arguments
        :type kwargs: dict

        :return: Redirection to the populated imprint form
        :rtype: ~django.http.HttpResponseRedirect
        """

        region = Region.get_current_region(request)
        language = get_object_or_404(region.languages, slug=kwargs.get("language_slug"))

        try:
            imprint_instance = region.imprint
        except ImprintPage.DoesNotExist:
            imprint_instance = None

        imprint_translation_instance = ImprintPageTranslation.objects.filter(
            page=imprint_instance,
            language=language,
        ).first()

        imprint_translation_form = ImprintTranslationForm(
            data=request.POST,
            instance=imprint_translation_instance,
            additional_instance_attributes={
                "creator": request.user,
                "language": language,
            },
        )

        if not imprint_translation_form.is_valid():
            # Add error messages
            imprint_translation_form.add_error_messages(request)
        elif (
            imprint_translation_form.instance.status == status.AUTO_SAVE
            and not imprint_form.has_changed()
            and not imprint_translation_form.has_changed()
        ):
            messages.info(request, _("No changes detected, autosave skipped"))
        else:
            # Create imprint instance if not exists
            imprint_translation_form.instance.page = (
                imprint_instance or ImprintPage.objects.create(region=region)
            )
            # Save form
            imprint_translation_form.save()
            # Add the success message and redirect to the edit page
            if not imprint_instance:
                messages.success(request, _("Imprint was successfully created"))
                return redirect(
                    "edit_imprint",
                    **{
                        "region_slug": region.slug,
                        "language_slug": language.slug,
                    },
                )
            # Add the success message
            imprint_translation_form.add_success_message(request)

        return render(
            request,
            self.template_name,
            {
                **self.base_context,
                "imprint_translation_form": imprint_translation_form,
                "imprint": imprint_instance,
                "language": language,
                # Languages for tab view
                "languages": region.languages if imprint_instance else [language],
                "side_by_side_language_options": self.get_side_by_side_language_options(
                    region, language, imprint_instance
                ),
            },
        )

    @staticmethod
    def get_side_by_side_language_options(region, language, imprint):
        """
        This is a helper function to generate the side-by-side language options for both the get and post requests.

        :param region: The current region
        :type region: ~cms.models.regions.region.Region

        :param language: The current language
        :type language: ~cms.models.languages.language.Language

        :param imprint: The current imprint
        :type imprint: ~cms.models.pages.imprint_page.ImprintPage

        :return: The list of language options, each represented by a dict
        :rtype: list
        """
        side_by_side_language_options = []
        for language_node in region.language_tree_nodes.all():
            if language_node.parent:
                source_translation = ImprintPageTranslation.objects.filter(
                    page=imprint,
                    language=language_node.parent.language,
                )
                side_by_side_language_options.append(
                    {
                        "value": language_node.language.slug,
                        "label": _("{source_language} to {target_language}").format(
                            source_language=language_node.parent.language.translated_name,
                            target_language=language_node.language.translated_name,
                        ),
                        "selected": language_node.language == language,
                        "disabled": not source_translation.exists(),
                    }
                )
        return side_by_side_language_options
