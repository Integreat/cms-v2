"""
This module contains the possible status of translations.
"""
from django.utils.translation import ugettext_lazy as _


#: Draft
DRAFT = "DRAFT"
#: Pending Review
REVIEW = "REVIEW"
#: Public
PUBLIC = "PUBLIC"
#: Auto Save
AUTO_SAVE = "AUTO_SAVE"

#: Choices to use these constants in a database field
CHOICES = (
    (DRAFT, _("Draft")),
    (REVIEW, _("Pending Review")),
    (PUBLIC, _("Published")),
    (AUTO_SAVE, _("Auto Save")),
)
