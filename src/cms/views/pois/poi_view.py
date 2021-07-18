"""
A view representing an instance of a point of interest. POIs can be created or updated via this view.
"""
import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView

from ...decorators import region_permission_required, permission_required
from ...forms import POIForm, POITranslationForm
from ...models import POI, POITranslation, Region, Language
from .poi_context_mixin import POIContextMixin
from ..media.media_context_mixin import MediaContextMixin


logger = logging.getLogger(__name__)


@method_decorator(login_required, name="dispatch")
@method_decorator(region_permission_required, name="dispatch")
@method_decorator(permission_required("cms.view_poi"), name="dispatch")
@method_decorator(permission_required("cms.change_poi"), name="post")
class POIView(TemplateView, POIContextMixin, MediaContextMixin):
    """
    View for editing POIs
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "pois/poi_form.html"
    #: The context dict passed to the template (see :class:`~django.views.generic.base.ContextMixin`)
    base_context = {"current_menu_item": "pois_form"}

    def get(self, request, *args, **kwargs):
        """
        Render :class:`~cms.forms.pois.poi_form.POIForm` and :class:`~cms.forms.pois.poi_translation_form.POITranslationForm`

        :param request: The current request
        :type request: ~django.http.HttpResponse

        :param args: The supplied arguments
        :type args: list

        :param kwargs: The supplied keyword arguments
        :type kwargs: dict

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """

        region = Region.get_current_region(request)
        language = Language.objects.get(slug=kwargs.get("language_slug"))

        # get poi and translation objects if they exist
        poi = POI.objects.filter(id=kwargs.get("poi_id")).first()
        poi_translation = POITranslation.objects.filter(
            poi=poi,
            language=language,
        ).first()

        if poi and poi.archived:
            disabled = True
            messages.warning(
                request, _("You cannot edit this location because it is archived.")
            )
        else:
            disabled = False

        poi_form = POIForm(instance=poi, disabled=disabled)
        poi_translation_form = POITranslationForm(
            instance=poi_translation, disabled=disabled
        )
        context = self.get_context_data(**kwargs)
        return render(
            request,
            self.template_name,
            {
                **self.base_context,
                **context,
                "poi_form": poi_form,
                "poi_translation_form": poi_translation_form,
                "language": language,
                # Languages for tab view
                "languages": region.languages if poi else [language],
            },
        )

    # pylint: disable=too-many-branches,too-many-locals,unused-argument
    def post(self, request, *args, **kwargs):
        """
        Submit :class:`~cms.forms.pois.poi_form.POIForm` and
        :class:`~cms.forms.pois.poi_translation_form.POITranslationForm` and save :class:`~cms.models.pois.poi.POI` and
        :class:`~cms.models.pois.poi_translation.POITranslation` objects

        :param request: The current request
        :type request: ~django.http.HttpResponse

        :param args: The supplied arguments
        :type args: list

        :param kwargs: The supplied keyword arguments
        :type kwargs: dict

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """

        region = Region.get_current_region(request)
        language = Language.objects.get(slug=kwargs.get("language_slug"))

        poi_instance = POI.objects.filter(id=kwargs.get("poi_id")).first()
        poi_translation_instance = POITranslation.objects.filter(
            poi=poi_instance,
            language=language,
        ).first()

        if poi_instance and poi_instance.archived:
            return redirect(
                "edit_poi",
                **{
                    "poi_id": poi_instance.id,
                    "region_slug": region.slug,
                    "language_slug": language.slug,
                }
            )

        poi_form = POIForm(
            data=request.POST,
            files=request.FILES,
            instance=poi_instance,
            additional_instance_attributes={
                "region": region,
            },
        )
        poi_translation_form = POITranslationForm(
            data=request.POST,
            instance=poi_translation_instance,
            additional_instance_attributes={
                "creator": request.user,
                "language": language,
                "poi": poi_form.instance,
            },
        )

        if not poi_form.is_valid() or not poi_translation_form.is_valid():
            # Add error messages
            poi_form.add_error_messages(request)
            poi_translation_form.add_error_messages(request)
        elif (
            poi_translation_form.instance.status == status.AUTO_SAVE
            and not poi_form.has_changed()
            and not poi_translation_form.has_changed()
        ):
            messages.info(request, _("No changes detected, autosave skipped"))
        else:
            # Save forms
            poi_translation_form.instance.poi = poi_form.save()
            poi_translation_form.save()
            # Add the success message and redirect to the edit page
            if not poi_instance:
                messages.success(
                    request,
                    _('Location "{}" was successfully created').format(
                        poi_translation_form.instance
                    ),
                )
                return redirect(
                    "edit_poi",
                    **{
                        "poi_id": poi_form.instance.id,
                        "region_slug": region.slug,
                        "language_slug": language.slug,
                    }
                )
            # Add the success message
            poi_translation_form.add_success_message(request)

        return render(
            request,
            self.template_name,
            {
                **self.base_context,
                **self.get_context_data(**kwargs),
                "poi_form": poi_form,
                "poi_translation_form": poi_translation_form,
                "language": language,
                # Languages for tab view
                "languages": region.languages if poi_instance else [language],
            },
        )
