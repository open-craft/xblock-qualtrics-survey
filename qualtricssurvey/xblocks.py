"""
This is the core logic for the XBlock
"""

from xblock.core import XBlock
from xblock.utils.settings import XBlockWithSettingsMixin

from .mixins.scenario import XBlockWorkbenchMixin
from .models import QualtricsSurveyModelMixin
from .views import QualtricsSurveyViewMixin


@XBlock.needs('i18n')
@XBlock.wants('user')
@XBlock.wants('settings')
class QualtricsSurvey(
        QualtricsSurveyModelMixin,
        QualtricsSurveyViewMixin,
        XBlockWithSettingsMixin,
        XBlockWorkbenchMixin,
        XBlock,
):
    """
    A Qualtrics survey XBlock.
    """

    block_settings_key = 'QualtricsSurvey'
