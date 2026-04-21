"""
Handle data access logic for the XBlock
"""

from django.utils.translation import gettext_lazy as _
from xblock.fields import Scope
from xblock.fields import String


class QualtricsSurveyModelMixin:
    """
    Handle data access for XBlock instances
    """

    editable_fields = [
        "display_name",
        "survey_id",
        "your_university",
        "link_text",
        "extra_params",
        "message",
    ]
    display_name = String(
        display_name=_("Display Name:"),
        default="Qualtrics Survey",
        scope=Scope.settings,
        help=_(
            "This name appears in the horizontal navigation at the top "
            "of the page."
        ),
    )
    link_text = String(
        display_name=_("Link Text:"),
        default="Begin Survey",
        scope=Scope.settings,
        help=_("This is the text that will link to your survey."),
    )
    message = String(
        display_name=_("Message:"),
        default="The survey will open in a new browser tab or window.",
        scope=Scope.settings,
        help=_(
            "This is the text that will be displayed "
            "above the link to your survey."
        ),
    )
    extra_params = String(
        display_name=_("Extra Parameters:"),
        default="",
        scope=Scope.settings,
        help=_(
            "Additional query parameters to include in the survey URL. "
            "Format: key1=value1&key2=value2. "
            "If blank, no extra parameters are added."
        ),
    )
    survey_id = String(
        display_name=_("Survey ID:"),
        default="Enter your survey ID here.",
        scope=Scope.settings,
        help=_(
            "This is the ID that Qualtrics uses for the survey, which can "
            "include numbers and letters, and should be entered in the "
            "following format: SV_###############"
        ),
    )
    your_university = String(
        display_name=_("Your University:"),
        default="",
        scope=Scope.settings,
        help=_(
            "The subdomain for your university's Qualtrics account "
            "(e.g.'stanforduniversity'). "
            "If left blank, the system-wide default is used."
        ),
    )
    # Deprecated: kept for backward compatibility with existing course data.
    # Not included in editable_fields so it no longer appears in Studio.
    param_name = String(
        default='',
        scope=Scope.settings,
    )
