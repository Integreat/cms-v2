from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView

from ...constants import translation_status
from ...decorators import region_permission_required
from ...forms import PageFilterForm
from ...models import Region, Language
from .page_context_mixin import PageContextMixin


@method_decorator(login_required, name="dispatch")
@method_decorator(region_permission_required, name="dispatch")
# pylint: disable=too-many-ancestors
class PageTreeView(PermissionRequiredMixin, TemplateView, PageContextMixin):
    """
    View for showing the page tree
    """

    #: Required permission of this view (see :class:`~django.contrib.auth.mixins.PermissionRequiredMixin`)
    permission_required = "cms.view_pages"
    #: Whether or not an exception should be raised if the user is not logged in (see :class:`~django.contrib.auth.mixins.LoginRequiredMixin`)
    raise_exception = True
    #: Template for list of non-archived pages
    template = "pages/page_tree.html"
    #: Template for list of archived pages
    template_archived = "pages/page_tree_archived.html"
    #: Whether or not to show archived pages
    archived = False

    @property
    def template_name(self):
        """
        Select correct HTML template, depending on :attr:`~cms.views.pages.page_tree_view.PageTreeView.archived` flag
        (see :class:`~django.views.generic.base.TemplateResponseMixin`)

        :return: Path to HTML template
        :rtype: str
        """

        return self.template_archived if self.archived else self.template

    # pylint: disable=too-many-locals
    def get(self, request, *args, **kwargs):
        """
        Render page tree

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
        region_slug = kwargs.get("region_slug")
        region = Region.get_current_region(request)

        # current language
        language_slug = kwargs.get("language_slug")
        if language_slug:
            language = Language.objects.get(slug=language_slug)
        elif region.default_language:
            return redirect(
                "pages",
                **{
                    "region_slug": region_slug,
                    "language_slug": region.default_language.slug,
                }
            )
        else:
            messages.error(
                request,
                _("Please create at least one language node before creating pages."),
            )
            return redirect(
                "language_tree",
                **{
                    "region_slug": region_slug,
                }
            )

        if not request.user.has_perm("cms.edit_page"):
            messages.warning(
                request, _("You don't have the permission to edit or create pages.")
            )
        context = self.get_context_data(**kwargs)

        pages = region.get_pages(archived=self.archived)
        enable_drag_and_drop = True
        # Filter pages according to given filters, if any
        filter_data = kwargs.get("filter_data")
        if filter_data:
            # Set data for filter form rendering
            filter_form = PageFilterForm(data=filter_data)
            if filter_form.is_valid():
                selected_status = filter_form.cleaned_data["translation_status"]
                # only filter if at least one checkbox but not all are checked
                if 0 < len(selected_status) < len(translation_status.CHOICES):
                    enable_drag_and_drop = False

                    def page_filter(page):
                        translation = page.get_translation(language_slug)
                        if not translation:
                            return translation_status.MISSING in selected_status
                        if translation.currently_in_translation:
                            return translation_status.IN_TRANSLATION in selected_status
                        if translation.is_outdated:
                            return translation_status.OUTDATED in selected_status
                        return translation_status.UP_TO_DATE in selected_status

                    pages = list(filter(page_filter, pages))
        else:
            filter_form = PageFilterForm()
            filter_form.changed_data.clear()

        if "xliff-download-url" in request.session:
            messages.success(
                request,
                _("XLIFF file successfully created.")
                + " "
                + _("If the download does not start automatically, please click")
                + " <a data-auto-download href='"
                + request.session["xliff-download-url"]
                + "' class='font-bold underline hover:no-underline'>"
                + _("here")
                + "</a>",
            )
            del request.session["xliff-download-url"]

        return render(
            request,
            self.template_name,
            {
                **context,
                "current_menu_item": "pages",
                "pages": pages,
                "archived_count": region.get_pages(archived=True).count(),
                "language": language,
                "languages": region.languages,
                "filter_form": filter_form,
                "enable_drag_and_drop": enable_drag_and_drop,
            },
        )

    def post(self, request, *args, **kwargs):
        """
        Apply page filters and render page tree

        :param request: The current request
        :type request: ~django.http.HttpResponse

        :param args: The supplied arguments
        :type args: list

        :param kwargs: The supplied keyword arguments
        :type kwargs: dict

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """
        return self.get(request, *args, **kwargs, filter_data=request.POST)
