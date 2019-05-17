import flywheel
import pytest
import mock
import run


class MockContainer(object):
    def __init__(self, container_type):
        self.container_type = container_type
        self.parents = mock.MagicMock(group='group_id')
        if container_type in ['subject', 'session', 'acquisition']:
            self.parents.project = 'project_id'
        if container_type in ['session', 'acquisition']:
            self.parents.subject = 'subject_id'
            self.project = 'project_id'
        if container_type == 'acquisition':
            self.parents.session = 'session_id'
        self.label = '{}_label'.format(container_type)
        self.id = '{}_id'.format(container_type)

class MockClient(object):
    def get_config(self):
        return mock.MagicMock(site=mock.MagicMock(api_url='https://hostname:port'))


def test_get_uri_for_project():
    client = MockClient()
    project = MockContainer('project')

    uri = run.get_uri(client, project)
    assert uri == 'https://hostname/#/projects/project_id'


def test_get_uri_for_subject():
    client = MockClient()
    subject = MockContainer('subject')

    uri = run.get_uri(client, subject)
    assert uri == 'https://hostname/#/projects/project_id'


def test_get_uri_for_session():
    client = MockClient()
    session = MockContainer('session')

    uri = run.get_uri(client, session)
    assert uri == 'https://hostname/#/projects/project_id/sessions/session_id?tab=data'


def test_get_uri_for_acquisition():
    client = MockClient()
    acquisition = MockContainer('acquisition')

    uri = run.get_uri(client, acquisition)
    assert uri == 'https://hostname/#/projects/project_id/sessions/session_id?tab=data'

