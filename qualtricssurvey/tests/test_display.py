#!/usr/bin/env python
"""
Test the Qualtrics Survey XBlock
"""
import unittest

from unittest import mock
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from xblock.field_data import DictFieldData
from xblock.reference.user_service import XBlockUser

from qualtricssurvey.xblocks import QualtricsSurvey


def make_user(
    user_id='12345', anonymous_id='anon-user-id', username='jdoe',
    emails=None,
):
    """
    Build an XBlockUser the way edx-platform does for an authenticated user.

    Pass ``None`` for any attribute to leave it unset, as happens for
    anonymous visitors.
    """
    user = XBlockUser(is_current_user=True, emails=emails)
    opt_attrs = {
        'edx-platform.user_id': user_id,
        'edx-platform.anonymous_user_id': anonymous_id,
        'edx-platform.username': username,
    }
    user.opt_attrs = {
        key: value for key, value in opt_attrs.items() if value is not None
    }
    return user


def mock_an_xblock(
    field_overrides=None, user=None, xblock_settings=None,
):
    """
    Create and return an instance of the XBlock
    """
    course_id = SlashSeparatedCourseKey('foo', 'bar', 'baz')
    runtime = mock.Mock(course_id=course_id)

    i18n_service = mock.Mock()
    i18n_service.ugettext.side_effect = lambda text: text
    i18n_service.gettext.side_effect = lambda text: text

    settings_service = mock.Mock()
    settings_service.get_settings_bucket.return_value = xblock_settings or {}

    user_service = mock.Mock()
    user_service.get_current_user.return_value = (
        user if user is not None else make_user()
    )

    def local_resource_url(_block, _path):
        return 'http://example.org/resource'

    runtime.local_resource_url = mock.Mock(side_effect=local_resource_url)

    def service(_block, service_name):
        if service_name == 'user':
            return user_service
        if service_name == 'i18n':
            return i18n_service
        if service_name == 'settings':
            return settings_service
        raise Exception('Service not available')

    runtime.service = mock.Mock(side_effect=service)

    scope_ids = mock.Mock()
    scope_ids.usage_id = 'usage-id'
    field_data = DictFieldData(field_overrides or {})
    return QualtricsSurvey(runtime, field_data, scope_ids)


class TestRender(unittest.TestCase):
    """
    Test the HTML rendering of the XBlock
    """

    def setUp(self):
        self.xblock = mock_an_xblock()

    def test_render(self):
        student_view = self.xblock.student_view()
        html = student_view.content
        self.assertIsNotNone(html)
        self.assertNotEqual('', html)
        self.assertIn('qualtricssurvey_block', html)

    def test_student_view_defaults(self):
        """
        Checks the default student view with no XBLOCK_SETTINGS configured.
        Since param_name defaults to '' and no USER_QUERY_PARAMS is set,
        no user params are sent.
        """
        xblock = self.xblock
        fragment = xblock.student_view()
        content = fragment.content
        self.assertIn('Begin Survey', content)
        self.assertIn('target="_blank"', content)
        self.assertNotIn('?', content)
        self.assertIn(xblock.message, content)

    def test_blank_param_name_sends_nothing(self):
        """
        When param_name is deliberately blank and no USER_QUERY_PARAMS
        is configured, no user params are sent. This respects a
        deliberate opt-out of user identification.
        """
        xblock = mock_an_xblock(
            field_overrides={'param_name': ''},
        )

        content = xblock.student_view().content

        self.assertNotIn('edxuid=', content)
        self.assertNotIn('anon-user-id', content)
        self.assertNotIn('?', content)

    def test_student_view_with_settings(self):
        """
        When USER_QUERY_PARAMS is configured in XBLOCK_SETTINGS,
        uses the configured mapping instead of legacy param_name.
        """
        xblock = mock_an_xblock(
            field_overrides={'extra_params': 'foo=bar&baz='},
            user=make_user(emails=['user@example.com']),
            xblock_settings={
                'USER_QUERY_PARAMS': {
                    'edxuid': 'user_id',
                    'email': 'email',
                },
            },
        )

        content = xblock.student_view().content

        self.assertIn('?edxuid=12345', content)
        self.assertIn('&amp;email=user%40example.com', content)
        self.assertIn('&amp;foo=bar', content)
        self.assertIn('&amp;baz=', content)
        self.assertNotIn('a=', content)

    def test_user_id_falls_back_to_anonymous_id(self):
        """
        When edx-platform.user_id is absent, user_id resolves to the
        anonymous ID instead.
        """
        xblock = mock_an_xblock(
            user=make_user(user_id=None),
            xblock_settings={'USER_QUERY_PARAMS': {'edxuid': 'user_id'}},
        )

        content = xblock.student_view().content

        self.assertIn('?edxuid=anon-user-id', content)

    def test_anonymous_visitor_sends_nothing(self):
        """
        edx-platform sets no identifying opt_attrs and no emails for
        unauthenticated users, so every user param is skipped.
        """
        xblock = mock_an_xblock(
            user=XBlockUser(is_current_user=True),
            xblock_settings={
                'USER_QUERY_PARAMS': {
                    'edxuid': 'user_id',
                    'anon': 'anonymous_id',
                    'email': 'email',
                    'uname': 'username',
                },
            },
        )

        content = xblock.student_view().content

        self.assertNotIn('?', content)

    def test_no_user_service_sends_nothing(self):
        """
        A runtime without a user service yields no user params.
        """
        xblock = mock_an_xblock(
            xblock_settings={'USER_QUERY_PARAMS': {'edxuid': 'user_id'}},
        )
        xblock.runtime.service = mock.Mock(return_value=None)

        content = xblock.student_view().content

        self.assertNotIn('?', content)

    def test_custom_user_query_params(self):
        """
        Checks that USER_QUERY_PARAMS from XBLOCK_SETTINGS controls which
        user attributes are sent and under what parameter names.
        """
        xblock = mock_an_xblock(
            user=make_user(user_id='99', emails=['j@example.com']),
            xblock_settings={
                'USER_QUERY_PARAMS': {
                    'uid': 'user_id',
                    'uname': 'username',
                },
            },
        )

        content = xblock.student_view().content

        self.assertIn('uid=99', content)
        self.assertIn('uname=jdoe', content)
        self.assertNotIn('email=', content)  # not in the mapping
        self.assertNotIn('edxuid=', content)  # overridden

    def test_anonymous_id_resolver(self):
        """
        USER_QUERY_PARAMS can explicitly request anonymous_id.
        """
        xblock = mock_an_xblock(
            xblock_settings={'USER_QUERY_PARAMS': {'anon': 'anonymous_id'}},
        )

        content = xblock.student_view().content

        self.assertIn('?anon=anon-user-id', content)

    def test_empty_user_query_params(self):
        """
        Setting USER_QUERY_PARAMS to empty dict disables all user params.
        """
        xblock = mock_an_xblock(
            xblock_settings={'USER_QUERY_PARAMS': {}},
        )

        content = xblock.student_view().content

        self.assertNotIn('edxuid=', content)
        self.assertNotIn('email=', content)
        self.assertNotIn('?', content)

    def test_unknown_attribute_key_skipped(self):
        """
        An unrecognized attribute key in USER_QUERY_PARAMS is silently skipped.
        """
        xblock = mock_an_xblock(
            xblock_settings={
                'USER_QUERY_PARAMS': {
                    'x': 'nonexistent_attribute',
                    'edxuid': 'user_id',
                },
            },
        )

        content = xblock.student_view().content

        self.assertNotIn('x=', content)
        self.assertIn('edxuid=12345', content)

    def test_param_name_backward_compat(self):
        """
        When no USER_QUERY_PARAMS is configured and the legacy param_name
        field has a value, fall back to {param_name: anonymous_id}.
        """
        xblock = mock_an_xblock(
            field_overrides={'param_name': 'a'},
        )

        content = xblock.student_view().content

        self.assertIn('?a=anon-user-id', content)
        self.assertNotIn('edxuid=', content)

    def test_param_name_overridden_by_settings(self):
        """
        When USER_QUERY_PARAMS is set in XBLOCK_SETTINGS, param_name is
        ignored even if it has a value.
        """
        xblock = mock_an_xblock(
            field_overrides={'param_name': 'a'},
            xblock_settings={
                'USER_QUERY_PARAMS': {'edxuid': 'user_id'},
            },
        )

        content = xblock.student_view().content

        self.assertIn('edxuid=12345', content)
        self.assertNotIn('a=', content)

    def test_university_from_settings_fallback(self):
        """
        When your_university field is blank, falls back to DEFAULT_UNIVERSITY
        from XBLOCK_SETTINGS.
        """
        xblock = mock_an_xblock(
            xblock_settings={'DEFAULT_UNIVERSITY': 'mit'},
        )

        content = xblock.student_view().content

        self.assertIn('https://mit.qualtrics.com', content)

    def test_university_field_takes_precedence(self):
        """
        When your_university field has a value, it takes precedence over
        DEFAULT_UNIVERSITY from XBLOCK_SETTINGS.
        """
        xblock = mock_an_xblock(
            field_overrides={'your_university': 'stanford'},
            xblock_settings={'DEFAULT_UNIVERSITY': 'mit'},
        )

        content = xblock.student_view().content

        self.assertIn('https://stanford.qualtrics.com', content)
        self.assertNotIn('mit', content)

    def test_extra_params(self):
        """
        Checks that extra_params are appended to the survey URL.
        """
        xblock = mock_an_xblock(
            field_overrides={'extra_params': 'course=CS101&term=fall'},
            xblock_settings={'USER_QUERY_PARAMS': {}},
        )

        content = xblock.student_view().content

        self.assertIn('course=CS101', content)
        self.assertIn('term=fall', content)

    def test_custom_message(self):
        """
        Checks the student view with a custom message.
        """
        message = 'test message'
        xblock = self.xblock
        xblock.message = message
        fragment = xblock.student_view()
        message_html = '<p>' + message + '</p>'
        content = fragment.content
        self.assertIn(message_html, content)


if __name__ == '__main__':
    unittest.main()
