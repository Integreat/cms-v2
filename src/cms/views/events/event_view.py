import logging

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.generic import TemplateView

from backend.settings import WEBAPP_URL

from ...constants import status
from ...decorators import region_permission_required, permission_required
from ...forms import EventForm, EventTranslationForm, RecurrenceRuleForm
from ...models import Region, Language, Event, EventTranslation, RecurrenceRule, POI
from .event_context_mixin import EventContextMixin
from ..media.media_context_mixin import MediaContextMixin


logger = logging.getLogger(__name__)


@method_decorator(login_required, name="dispatch")
@method_decorator(region_permission_required, name="dispatch")
@method_decorator(permission_required("cms.view_event"), name="dispatch")
@method_decorator(permission_required("cms.change_event"), name="post")
class EventView(TemplateView, EventContextMixin, MediaContextMixin):
    """
    Class for rendering the events form
    """

    #: The template to render (see :class:`~django.views.generic.base.TemplateResponseMixin`)
    template_name = "events/event_form.html"

    # pylint: disable=too-many-locals
    def get(self, request, *args, **kwargs):
        """
        Render event form for HTTP GET requests

        :param request: Object representing the user call
        :type request: ~django.http.HttpRequest

        :param args: The supplied arguments
        :type args: list

        :param kwargs: The supplied keyword arguments
        :type kwargs: dict

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """
        region = Region.get_current_region(request)
        language = get_object_or_404(region.languages, slug=kwargs.get("language_slug"))

        # get event and event translation objects if they exist, otherwise objects are None
        event_instance = region.events.filter(id=kwargs.get("event_id")).first()
        event_translation_instance = language.event_translations.filter(
            event=event_instance
        ).first()
        recurrence_rule_instance = RecurrenceRule.objects.filter(
            event=event_instance
        ).first()
        poi_instance = region.pois.filter(events=event_instance).first()

        # Make form disabled if event is archived or user doesn't have the permission to edit the event
        if event_instance and event_instance.archived:
            disabled = True
            messages.warning(
                request, _("You cannot edit this event because it is archived.")
            )
        elif not request.user.has_perm("cms.change_event"):
            disabled = True
            messages.warning(
                request, _("You don't have the permission to edit events.")
            )
        else:
            disabled = False

        if not request.user.has_perm("cms.publish_event"):
            messages.warning(
                request,
                _(
                    "You don't have the permission to publish events, but you can propose changes and submit them for review instead."
                ),
            )

        event_form = EventForm(instance=event_instance, disabled=disabled)
        event_translation_form = EventTranslationForm(
            instance=event_translation_instance, disabled=disabled
        )
        recurrence_rule_form = RecurrenceRuleForm(
            instance=recurrence_rule_instance, disabled=disabled
        )
        context = self.get_context_data(**kwargs)
        url_link = f"{WEBAPP_URL}/{region.slug}/{language.slug}/events/"
        return render(
            request,
            self.template_name,
            {
                **context,
                "current_menu_item": "events_form",
                "event_form": event_form,
                "event_translation_form": event_translation_form,
                "recurrence_rule_form": recurrence_rule_form,
                "poi": poi_instance,
                "language": language,
                "languages": region.languages if event_instance else [language],
                "url_link": url_link,
            },
        )

    # pylint: disable=too-many-locals,too-many-branches
    def post(self, request, **kwargs):
        """
        Save event and ender event form for HTTP POST requests

        :param request: Object representing the user call
        :type request: ~django.http.HttpRequest

        :param kwargs: The supplied keyword arguments
        :type kwargs: dict

        :raises ~django.core.exceptions.PermissionDenied: If user does not have the permission to publish events

        :return: The rendered template response
        :rtype: ~django.template.response.TemplateResponse
        """
        region = Region.get_current_region(request)
        language = Language.objects.get(slug=kwargs.get("language_slug"))
        poi = POI.objects.filter(id=request.POST.get("poi_id")).first()

        event_instance = Event.objects.filter(id=kwargs.get("event_id")).first()
        recurrence_rule_instance = RecurrenceRule.objects.filter(
            event=event_instance
        ).first()
        event_translation_instance = EventTranslation.objects.filter(
            event=event_instance, language=language
        ).first()

        event_form = EventForm(
            data=request.POST,
            files=request.FILES,
            instance=event_instance,
            additional_instance_attributes={"region": region, "location": poi},
        )
        # clean data of event form to be able to pass the cleaned start date to the recurrence form for validation
        event_form_valid = event_form.is_valid()
        recurrence_rule_form = RecurrenceRuleForm(
            data=request.POST,
            instance=recurrence_rule_instance,
            event_start_date=event_form.cleaned_data.get("start_date", None),
        )
        event_translation_form = EventTranslationForm(
            data=request.POST,
            instance=event_translation_instance,
            additional_instance_attributes={
                "creator": request.user,
                "language": language,
                "event": event_form.instance,
            },
        )

        if (
            not event_form_valid
            or not event_translation_form.is_valid()
            or (
                event_form.cleaned_data["is_recurring"]
                and not recurrence_rule_form.is_valid()
            )
        ):
            # Add error messages
            event_form.add_error_messages(request)
            event_translation_form.add_error_messages(request)
            recurrence_rule_form.add_error_messages(request)
        elif (
            event_translation_form.instance.status == status.AUTO_SAVE
            and not event_form.has_changed()
            and not event_translation_form.has_changed()
        ):
            messages.info(request, _("No changes detected, autosave skipped"))
        else:
            # Check publish permissions
            if event_translation_form.instance.status == status.PUBLIC:
                if not request.user.has_perm("cms.publish_event"):
                    raise PermissionDenied(
                        f"{request.user.profile!r} does not have the permission 'cms.publish_event'"
                    )
            # Save forms
            if event_form.cleaned_data.get("is_recurring"):
                # If event is recurring, save recurrence rule
                event_form.instance.recurrence_rule = recurrence_rule_form.save()
            elif event_form.fields["is_recurring"].has_changed():
                # If the event is not recurring but it was before, delete the associated recurrence rule
                event_form.instance.recurrence_rule.delete()
            event_translation_form.instance.event = event_form.save()
            event_translation_form.save()
            # Add the success message and redirect to the edit page
            if not event_instance:
                messages.success(
                    request,
                    _('Event "{}" was successfully created').format(
                        event_translation_form.instance
                    ),
                )
                return redirect(
                    "edit_event",
                    **{
                        "event_id": event_form.instance.id,
                        "region_slug": region.slug,
                        "language_slug": language.slug,
                    },
                )
            # Add the success message
            event_translation_form.add_success_message(request)

        return render(
            request,
            self.template_name,
            {
                **self.get_context_data(**kwargs),
                "current_menu_item": "events",
                "event_form": event_form,
                "event_translation_form": event_translation_form,
                "recurrence_rule_form": recurrence_rule_form,
                "poi": poi,
                "language": language,
                "languages": region.languages if event_instance else [language],
            },
        )
