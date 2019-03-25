import flywheel
import pytest
import run as grp


class MockClient(object):
    def __init__(self, set_error):
        self.containers = {}
        self.set_error = set_error

    def get_container(self, _id):
        if self.containers.get(_id):
            return self.containers[_id]
        else:
            if self.set_error:
                container = MockContainer(['error.log'], ['error'], _id)
            else:
                container = MockContainer([], [], _id)
            self.containers[_id] = container
            return container


class MockContainer(object):
    def __init__(self, files, tags, _id):
        self.files = files
        self.tags = tags
        self.container_type = 'container'
        self.id = _id
    def get_file(self, name):
        if name in self.files:
            return name
        else:
            return None
    def delete_file(self, name):
        if name in self.files:
            self.files.remove(name)
        else:
            raise flywheel.ApiException(status=404)
    def delete_tag(self, name):
        if name in self.tags:
            self.tags.remove(name)
        else:
            raise flywheel.ApiException(status=404)


def test_set_resolved_true():
    client = MockClient(True)
    validator = lambda x: True
    error_containers = [
        {'_id': 'container_id'}
    ]
    container = client.get_container('container_id')

    assert container.files == ['error.log']
    assert container.tags == ['error']

    grp.set_resolved_status(error_containers, client, validator)
    container = client.get_container('container_id')

    assert error_containers[0]['resolved'] is True
    assert container.files == []
    assert container.tags == []


def test_set_resolved_false():
    client = MockClient(True)
    validator = lambda x: False
    error_containers = [
        {'_id': 'container_id'}
    ]
    container = client.get_container('container_id')

    assert container.files == ['error.log']
    assert container.tags == ['error']

    grp.set_resolved_status(error_containers, client, validator)
    container = client.get_container('container_id')

    assert error_containers[0]['resolved'] is False
    assert container.files == ['error.log']
    assert container.tags == ['error']


def test_set_resolved_true_no_file():
    client = MockClient(True)
    validator = lambda x: True
    error_containers = [
        {'_id': 'container_id'}
    ]
    container = client.get_container('container_id')
    container.files = []

    assert container.files == []
    assert container.tags == ['error']

    grp.set_resolved_status(error_containers, client, validator)
    container = client.get_container('container_id')

    assert error_containers[0]['resolved'] is True
    assert container.files == []
    assert container.tags == []

