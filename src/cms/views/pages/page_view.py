import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView

from ...constants import status, text_directions
from ...decorators import region_permission_required, permission_required
from ...forms import PageForm, PageTranslationForm
from ...models import PageTranslation, Region
from .page_context_mixin import PageContextMixin
from ..media.media_context_mixin import MediaContextMixin

logger = logging.getLogger(__name__)


@method_decorator(login_required, name="dispatch")
@method_decorator(region_permission_required, name="dispatch")
@method_decorator(permission_required("cms.view_page"), name="dispatch")
class PageView(TemplateView, PageContextMixin, MediaContextMixin):
    """
    View for the page form and page translation form
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "pages/page_form.html"
    #: The context dict passed to the template (see :class:`~django.views.generic.base.ContextMixin`)
    base_context = {
        "current_menu_item": "new_page",
        "PUBLIC": status.PUBLIC,
    }

    # pylint: disable=too-many-locals
    def get(self, request, *args, **kwargs):
        """
        Render :class:`~cms.forms.pages.page_form.PageForm` and :class:`~cms.forms.pages.page_translation_form.PageTranslationForm`

        :param request: The current request
        :type request: ~django.http.HttpResponse

        :param args: The supplied arguments
        :type args: list

        :param kwargs: The supplied keyword arguments
        :type kwargs: dict

        :raises ~django.core.exceptions.PermissionDenied: If user does not have the permission to edit the specific page

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """

        region = Region.get_current_region(request)
        language = get_object_or_404(region.languages, slug=kwargs.get("language_slug"))

        # get page and translation objects if they exist
        page = region.pages.filter(id=kwargs.get("page_id")).first()
        page_translation = PageTranslation.objects.filter(
            page=page,
            language=language,
        ).first()

        disabled = False
        if page:
            # Make form disabled if page is archived
            if page.explicitly_archived:
                disabled = True
                messages.warning(
                    request, _("You cannot edit this page because it is archived.")
                )
            elif page.implicitly_archived:
                disabled = True
                messages.warning(
                    request,
                    _(
                        "You cannot edit this page, because one of its parent pages is archived and therefore, this page is archived as well."
                    ),
                )
            # Show information if latest changes are only saved as draft
            public_translation = page.get_public_translation(language.slug)
            if public_translation and page_translation != public_translation:
                messages.info(
                    request,
                    _(
                        "The latest changes have only been saved as a draft. Currently, <a href='%(revision_url)s' class='underline hover:no-underline'>version %(revision)s</a> of this page is displayed in the app."
                    )
                    % {
                        "revision_url": reverse(
                            "page_revisions",
                            kwargs={
                                "region_slug": region.slug,
                                "language_slug": language.slug,
                                "page_id": page.id,
                                "selected_revision": public_translation.version,
                            },
                        ),
                        "revision": public_translation.version,
                    },
                )

        # Make form disabled if user has no permission to edit the page
        if not request.user.has_perm("cms.change_page_object", page):
            disabled = True
            messages.warning(
                request,
                _("You don't have the permission to edit this page."),
            )
        # Show warning if user has no permission to publish the page
        if not request.user.has_perm("cms.publish_page_object", page):
            messages.warning(
                request,
                _(
                    "You don't have the permission to publish this page, but you can propose changes and submit them for review instead."
                ),
            )

        page_form = PageForm(
            instance=page,
            disabled=disabled,
            additional_instance_attributes={
                "region": region,
            },
        )
        page_translation_form = PageTranslationForm(
            instance=page_translation, disabled=disabled
        )

        # Pass side by side language options
        side_by_side_language_options = self.get_side_by_side_language_options(
            region, language, page
        )

        # Pass siblings to template to enable rendering of page order table
        if not page or not page.parent:
            siblings = region.pages.filter(level=0)
        else:
            siblings = page.parent.children.all()
        context = self.get_context_data(**kwargs)
        return render(
            request,
            self.template_name,
            {
                **self.base_context,
                **context,
                "page_form": page_form,
                "page_translation_form": page_translation_form,
                "page": page,
                "siblings": siblings,
                "language": language,
                # Languages for tab view
                "languages": region.languages if page else [language],
                "side_by_side_language_options": side_by_side_language_options,
                "right_to_left": (
                    language.text_direction == text_directions.RIGHT_TO_LEFT
                ),
            },
        )

    # pylint: disable=too-many-branches,unused-argument
    def post(self, request, *args, **kwargs):
        """
        Submit :class:`~cms.forms.pages.page_form.PageForm` and
        :class:`~cms.forms.pages.page_translation_form.PageTranslationForm` and save :class:`~cms.models.pages.page.Page`
        and :class:`~cms.models.pages.page_translation.PageTranslation` objects.
        Forms containing images/files need to be additionally instantiated with the FILES attribute of request objects,
        see :doc:`django:topics/http/file-uploads`

        :param request: The current request
        :type request: ~django.http.HttpResponse

        :param args: The supplied arguments
        :type args: list

        :param kwargs: The supplied keyword arguments
        :type kwargs: dict

        :raises ~django.core.exceptions.PermissionDenied: If user does not have the permission to edit the specific page

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """

        region = Region.get_current_region(request)
        language = get_object_or_404(region.languages, slug=kwargs.get("language_slug"))

        page_instance = region.pages.filter(id=kwargs.get("page_id")).first()

        if not request.user.has_perm("cms.change_page_object", page_instance):
            raise PermissionDenied(
                f"{request.user.profile!r} does not have the permission to edit {page_instance!r}"
            )

        page_translation_instance = PageTranslation.objects.filter(
            page=page_instance,
            language=language,
        ).first()

        # Pass siblings to template to enable rendering of page order table
        if not page_instance or not page_instance.parent:
            siblings = region.pages.filter(level=0)
        else:
            siblings = page_instance.parent.children.all()

        page_form = PageForm(
            data=request.POST,
            files=request.FILES,
            instance=page_instance,
            additional_instance_attributes={
                "region": region,
            },
        )
        page_translation_form = PageTranslationForm(
            data=request.POST,
            instance=page_translation_instance,
            additional_instance_attributes={
                "creator": request.user,
                "language": language,
                "page": page_form.instance,
            },
        )

        if not page_form.is_valid() or not page_translation_form.is_valid():
            # Add error messages
            page_form.add_error_messages(request)
            page_translation_form.add_error_messages(request)
        elif (
            not request.user.has_perm("cms.publish_page_object", page_form.instance)
            and page_translation_form.cleaned_data.get("status") == status.PUBLIC
        ):
            # Raise PermissionDenied if user wants to publish page but doesn't have the permission
            raise PermissionDenied(
                f"{request.user.profile!r} does not have the permission to publish {page_form.instance!r}"
            )
        elif (
            page_translation_form.instance.status == status.AUTO_SAVE
            and not page_form.has_changed()
            and not page_translation_form.has_changed()
        ):
            messages.info(request, _("No changes detected, autosave skipped"))

        else:
            # Save forms
            page_translation_form.instance.page = page_form.save()
            page_translation_form.save()
            # Add the success message and redirect to the edit page
            if not page_instance:
                messages.success(
                    request,
                    _('Page "{}" was successfully created').format(
                        page_translation_form.instance.title
                    ),
                )
                return redirect(
                    "edit_page",
                    **{
                        "page_id": page_form.instance.id,
                        "region_slug": region.slug,
                        "language_slug": language.slug,
                    },
                )

            if not page_form.has_changed() and not page_translation_form.has_changed():
                messages.info(request, _("No changes detected, but date refreshed"))
            else:
                # Add the success message
                page_translation_form.add_success_message(request)

        return render(
            request,
            self.template_name,
            {
                **self.base_context,
                "page_form": page_form,
                "page_translation_form": page_translation_form,
                "page": page_instance,
                "siblings": siblings,
                "language": language,
                # Languages for tab view
                "languages": region.languages if page_instance else [language],
                "side_by_side_language_options": self.get_side_by_side_language_options(
                    region, language, page_instance
                ),
                "right_to_left": (
                    language.text_direction == text_directions.RIGHT_TO_LEFT
                ),
            },
        )

    @staticmethod
    def get_side_by_side_language_options(region, language, page):
        """
        This is a helper function to generate the side-by-side language options for both the get and post requests.

        :param region: The current region
        :type region: ~cms.models.regions.region.Region

        :param language: The current language
        :type language: ~cms.models.languages.language.Language

        :param page: The current page
        :type page: ~cms.models.pages.page.Page

        :return: The list of language options, each represented by a dict
        :rtype: list
        """

        side_by_side_language_options = []
        for language_node in region.language_tree_nodes.all():
            if language_node.parent:
                source_translation = PageTranslation.objects.filter(
                    page=page,
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
