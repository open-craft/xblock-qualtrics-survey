Qualtrics Survey
==================

XBlock to ease linking to Qualtrics surveys.

|badge-ci|
|badge-coveralls|

The tool makes it easy for instructors to link to a Qualtrics survey
from within their course.

|image-lms-view-normal|


Installation
------------


System Administrator
~~~~~~~~~~~~~~~~~~~~

To install the XBlock on your platform,
add the following to your `requirements.txt` file:

    xblock-qualtrics-survey

You'll also need to add this to your `INSTALLED_APPS`:

    qualtricssurvey


Course Staff
~~~~~~~~~~~~

To install the XBlock in your course,
access your `Advanced Module List`:

    Settings -> Advanced Settings -> Advanced Module List

|image-cms-settings-menu|

and add the following:

    qualtricssurvey

|image-cms-advanced-module-list|


Use
---


Course Staff
~~~~~~~~~~~~

To add a Qualtrics Survey link to your course:

- go to a unit in Studio
- select "Qualtrics Survey" from the Advanced Components menu

|image-cms-add|

You can now edit and preview the new component.

|image-cms-view|

Using the Studio editor, you can edit the following fields:

- display name
- survey id
- university
- link text
- extra parameters
- message

|image-cms-editor-1|
|image-cms-editor-2|


Configuration
~~~~~~~~~~~~~

Operators can configure system-wide defaults via ``XBLOCK_SETTINGS`` in
the Django settings:

.. code-block:: python

    XBLOCK_SETTINGS["QualtricsSurvey"] = {
        "DEFAULT_UNIVERSITY": "pennstate",
        "USER_QUERY_PARAMS": {
            "edxuid": "user_id",
            "email": "email",
        },
    }

``DEFAULT_UNIVERSITY``
    The default Qualtrics subdomain for your institution. Used when the
    per-instance university field is left blank.

``USER_QUERY_PARAMS``
    A mapping of URL parameter names to user attributes. The key is the
    query parameter name that appears in the survey URL, and the value is
    the user attribute to resolve. Supported attributes:

    - ``user_id`` -- platform user ID (with fallback to anonymous ID)
    - ``anonymous_id`` -- anonymous student identifier
    - ``email`` -- primary email address
    - ``username`` -- platform username

    If ``USER_QUERY_PARAMS`` is not configured, no user parameters are
    sent by default. To start sending user data to Qualtrics, operators
    must explicitly configure this setting.


Participants
~~~~~~~~~~~~

|image-lms-view-normal|

Students click on a link within the unit and this takes them to the survey.


.. |badge-coveralls| image:: https://coveralls.io/repos/github/Stanford-Online/xblock-qualtrics-survey/badge.svg?branch=master
   :target: https://coveralls.io/github/Stanford-Online/xblock-qualtrics-survey?branch=master
.. |badge-ci| image:: https://github.com/openedx/xblock-qualtrics-survey/workflows/Python%20CI/badge.svg?branch=master
   :target: https://github.com/openedx/xblock-qualtrics-survey/actions?query=workflow%3A%22Python+CI%22
.. |image-cms-add| image:: https://s3-us-west-1.amazonaws.com/stanford-openedx-docs/xblocks/qualtrics-survey/static/images/cms-add.png
   :width: 100%
.. |image-cms-advanced-module-list| image:: https://s3-us-west-1.amazonaws.com/stanford-openedx-docs/xblocks/qualtrics-survey/static/images/cms-advanced-module-list.png
   :width: 100%
.. |image-cms-editor-1| image:: https://s3-us-west-1.amazonaws.com/stanford-openedx-docs/xblocks/qualtrics-survey/static/images/cms-editor-1.png
   :width: 100%
.. |image-cms-editor-2| image:: https://s3-us-west-1.amazonaws.com/stanford-openedx-docs/xblocks/qualtrics-survey/static/images/cms-editor-2.png
   :width: 100%
.. |image-cms-settings-menu| image:: https://s3-us-west-1.amazonaws.com/stanford-openedx-docs/xblocks/qualtrics-survey/static/images/cms-settings-menu.png
   :width: 100%
.. |image-cms-view| image:: https://s3-us-west-1.amazonaws.com/stanford-openedx-docs/xblocks/qualtrics-survey/static/images/cms-view.png
   :width: 100%
.. |image-lms-view-normal| image:: https://s3-us-west-1.amazonaws.com/stanford-openedx-docs/xblocks/qualtrics-survey/static/images/lms-view-normal.png
   :width: 100%
