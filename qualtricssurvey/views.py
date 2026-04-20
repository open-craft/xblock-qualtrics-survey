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


DEFAULT_USER_QUERY_PARAMS = {
    'edxuid': 'user_id',
    'email': 'email',
}


def _resolve_user_id(xblock, user, runtime):
    """Resolve the platform user ID with fallbacks."""
    if user:
        user_id = user.user_id or user.opt_attrs.get('edx-platform.user_id')
        if user_id:
            return user_id
    return _resolve_anonymous_id(xblock, user, runtime)


def _resolve_anonymous_id(xblock, _user, runtime):
    """Resolve the anonymous student ID."""
    return (
        getattr(runtime, 'anonymous_student_id', None)
        or getattr(
            getattr(xblock, 'xmodule_runtime', None),
            'anonymous_student_id', None,
        )
    )


def _resolve_email(_xblock, user, _runtime):
    """Resolve the primary email address."""
    return user.emails[0] if user and user.emails else None


def _resolve_username(_xblock, user, _runtime):
    """Resolve the platform username."""
    return user.opt_attrs.get('edx-platform.username') if user else None


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
        runtime = getattr(self, 'runtime', None)
        if not runtime:
            return params

        try:
            user_service = runtime.service(self, 'user')
        except Exception:  # pragma: no cover - service may be unavailable
            user_service = None

        user = user_service.get_current_user() if user_service else None

        if 'USER_QUERY_PARAMS' not in settings and self.param_name:
            # fallback: use the old param_name -> anonymous_id behavior
            param_map = {self.param_name: 'anonymous_id'}
        else:
            param_map = settings.get(
                'USER_QUERY_PARAMS', DEFAULT_USER_QUERY_PARAMS,
            )

        for url_param_name, attribute_key in param_map.items():
            resolver = USER_ATTRIBUTE_RESOLVERS.get(attribute_key)
            if not resolver:
                continue
            value = resolver(self, user, runtime)
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
