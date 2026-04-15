#!/usr/bin/env python
"""
Test the Qualtrics Survey XBlock
"""
import unittest

from unittest import mock
from opaque_keys.edx.locations import SlashSeparatedCourseKey
from xblock.field_data import DictFieldData

from qualtricssurvey.xblocks import QualtricsSurvey


def mock_an_xblock(field_overrides=None, user_service=None, xblock_settings=None):
    """
    Create and return an instance of the XBlock
    """
    course_id = SlashSeparatedCourseKey('foo', 'bar', 'baz')
    runtime = mock.Mock(course_id=course_id)
    runtime.anonymous_student_id = 'anon-user-id'

    i18n_service = mock.Mock()
    i18n_service.ugettext.side_effect = lambda text: text
    i18n_service.gettext.side_effect = lambda text: text

    settings_service = mock.Mock()
    settings_service.get_settings_bucket.return_value = xblock_settings or {}

    def local_resource_url(_block, _path):
        return 'http://example.org/resource'

    runtime.local_resource_url = mock.Mock(side_effect=local_resource_url)

    def service(_block, service_name):
        if service_name == 'user' and user_service is not None:
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
    xblock = QualtricsSurvey(runtime, field_data, scope_ids)
    xblock.xmodule_runtime = runtime
    return xblock


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
        Since param_name defaults to 'a' and no USER_QUERY_PARAMS is set,
        the legacy fallback sends {param_name: anonymous_id}.
        """
        xblock = self.xblock
        fragment = xblock.student_view()
        content = fragment.content
        self.assertIn('Begin Survey', content)
        self.assertIn('target="_blank"', content)
        self.assertIn('?a=anon-user-id', content)
        self.assertIn(xblock.message, content)

    def test_student_view_with_settings(self):
        """
        When USER_QUERY_PARAMS is configured in XBLOCK_SETTINGS,
        uses the configured mapping instead of legacy param_name.
        """
        xblock = mock_an_xblock(
            xblock_settings={
                'USER_QUERY_PARAMS': {
                    'edxuid': 'user_id',
                    'email': 'email',
                },
            },
        )
        content = xblock.student_view().content
        self.assertIn('?edxuid=anon-user-id', content)
        self.assertNotIn('a=', content)

    def test_student_view_with_user_service(self):
        """
        Checks the student view when the runtime provides user information
        and USER_QUERY_PARAMS is configured.
        """
        user = mock.Mock()
        user.user_id = None
        user.opt_attrs = {
            'edx-platform.user_id': '12345',
        }
        user.emails = ['user@example.com']
        user_service = mock.Mock()
        user_service.get_current_user.return_value = user
        xblock = mock_an_xblock(
            field_overrides={'extra_params': 'foo=bar&baz='},
            user_service=user_service,
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

    def test_custom_user_query_params(self):
        """
        Checks that USER_QUERY_PARAMS from XBLOCK_SETTINGS controls which
        user attributes are sent and under what parameter names.
        """
        user = mock.Mock()
        user.user_id = '99'
        user.opt_attrs = {'edx-platform.username': 'jdoe'}
        user.emails = ['j@example.com']
        user_service = mock.Mock()
        user_service.get_current_user.return_value = user
        xblock = mock_an_xblock(
            user_service=user_service,
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
        self.assertIn('edxuid=anon-user-id', content)

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

        self.assertIn('edxuid=anon-user-id', content)
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
