"""
Handle view logic for the XBlock
"""
from urllib.parse import parse_qsl
from urllib.parse import urlencode

try:
    from xblock.utils.resources import ResourceLoader
    from xblock.utils.studio_editable import StudioEditableXBlockMixin
except ModuleNotFoundError:
    # For backward compatibility with releases older than Quince.
    from xblockutils.resources import ResourceLoader
    from xblockutils.studio_editable import StudioEditableXBlockMixin

from .mixins.fragment import XBlockFragmentBuilderMixin


# Keys that edx-platform sets on ``XBlockUser.opt_attrs``. They are only
# present for authenticated users; anonymous visitors get none of them.
ATTR_KEY_USER_ID = 'edx-platform.user_id'
ATTR_KEY_ANONYMOUS_USER_ID = 'edx-platform.anonymous_user_id'
ATTR_KEY_USERNAME = 'edx-platform.username'


def _resolve_user_id(user):
    """Resolve the platform user ID, falling back to the anonymous ID."""
    return _opt_attr(user, ATTR_KEY_USER_ID) or _resolve_anonymous_id(user)


def _resolve_anonymous_id(user):
    """Resolve the course-specific anonymous user ID."""
    return _opt_attr(user, ATTR_KEY_ANONYMOUS_USER_ID)


def _resolve_email(user):
    """Resolve the primary email address."""
    return user.emails[0] if user and user.emails else None


def _resolve_username(user):
    """Resolve the platform username."""
    return _opt_attr(user, ATTR_KEY_USERNAME)


def _opt_attr(user, key):
    """Read an optional attribute from the user, or None if unavailable."""
    return user.opt_attrs.get(key) if user else None


USER_ATTRIBUTE_RESOLVERS = {
    'user_id': _resolve_user_id,
    'anonymous_id': _resolve_anonymous_id,
    'email': _resolve_email,
    'username': _resolve_username,
}


class QualtricsSurveyViewMixin(
        XBlockFragmentBuilderMixin,
        StudioEditableXBlockMixin,
):
    """
    Handle view logic for the XBlock
    """

    loader = ResourceLoader(__name__)
    show_in_read_only_mode = True

    def provide_context(self, context=None):
        """
        Build a context dictionary to render the student view
        """
        context = context or {}
        context = dict(context)
        settings = self.get_xblock_settings(default={})
        query_params = self._user_query_params(settings)
        query_params.extend(self._extra_query_params())
        query_string = ''
        if query_params:
            query_string = f"?{urlencode(query_params, doseq=True)}"
        university = (
            self.your_university
            or settings.get('DEFAULT_UNIVERSITY', '')
        )
        context.update({
            'xblock_id': str(self.scope_ids.usage_id),
            'survey_id': self.survey_id,
            'your_university': university,
            'link_text': self.link_text,
            'query_string': query_string,
            'message': self.message,
        })
        return context

    def _user_query_params(self, settings):
        """
        Return query parameters derived from the current user.
        """
        params = []
        user_service = self.runtime.service(self, 'user')
        user = user_service.get_current_user() if user_service else None

        if 'USER_QUERY_PARAMS' in settings:
            param_map = settings['USER_QUERY_PARAMS']
        elif self.param_name:
            # Legacy fallback: use the old param_name -> anonymous_id
            param_map = {self.param_name: 'anonymous_id'}
        else:
            # No settings configured and param_name is blank, send
            # nothing.
            param_map = {}

        for url_param_name, attribute_key in param_map.items():
            resolver = USER_ATTRIBUTE_RESOLVERS.get(attribute_key)
            if not resolver:
                continue
            value = resolver(user)
            if value:
                params.append((url_param_name, value))

        return params

    def _extra_query_params(self):
        """
        Return query parameters defined by the author.
        """
        extra_params = getattr(self, 'extra_params', '') or ''
        extra_params = extra_params.strip()
        if not extra_params:
            return []

        cleaned = extra_params.lstrip('&?')
        if not cleaned:
            return []

        parsed = parse_qsl(cleaned, keep_blank_values=True)
        return parsed
