import json
import logging
from pathlib import Path

import pytest
import mock
import run


DATA_ROOT = Path(__file__).parent.parent / 'data'


def test_validate_required_exists_valid():
    error = {
        'revalidate': True,
        'schema': {
            'type': 'string'
        },
        'item': 'label'
    }
    container = {'label': 'STRING'}

    error_status = run.validate(container, error)
    assert error_status == list()


def test_validate_required_exists_invalid():
    error = {
        'revalidate': True,
        'schema': {
            'type': 'string'
        },
        'item': 'label'
    }
    container = {'label': 1}

    error_status = run.validate(container, error)
    assert error_status == ['1 is not of type \'string\'']


def test_validate_required_does_not_exist():
    error = {
        'revalidate': True,
        'schema': {
            'required': ['label']
        },
        'item': 'info'
    }
    container = {'info': {}}

    error_status = run.validate(container, error)
    assert error_status == ['\'label\' is a required property']


def test_validate_exists_valid():
    error = {
        'revalidate': True,
        'schema': {
            'type': 'string'
        },
        'item': 'label'
    }
    container = {'label': 'STRING'}

    error_status = run.validate(container, error)
    assert error_status == list()


def test_validate_exists_invalid():
    error = {
        'revalidate': True,
        'schema': {
            'type': 'string'
        },
        'item': 'label'
    }
    container = {'label': 1}

    error_status = run.validate(container, error)
    assert error_status == ['1 is not of type \'string\'']


def test_validate_item_does_not_exist(caplog):
    error = {
        'revalidate': True,
        'schema': {
            'required': ['label']
        },
        'item': 'info'
    }
    container = {'name': 'test.dcm'}
    with caplog.at_level(logging.WARNING):
        error_status = run.validate(container, error)
        assert error_status[0].endswith('Please confirm metadata are not missing.')
        assert any([message.endswith('Please confirm metadata are not missing.') for message in caplog.messages])


def test_not_revalidate():
    error = {
        'revalidate': False,
    }
    container = {}

    error_status = run.validate(container, error)
    assert error_status == ['Skipping revalidation']


def test_not_revalidate_message():
    error = {
        'revalidate': False,
        'error_message': 'Not enough images'
    }
    container = {}

    error_status = run.validate(container, error)
    assert error_status == ['Not enough images']


def test_get_schema_errors_no_errors():
    assert run.get_schema_errors({}, {}) == list()


def test_get_schema_errors_required():
    err_list = run.get_schema_errors({}, {'required': ['cats']})
    assert err_list == ["'cats' is a required property"]


def test_fail_all_validate():
    error_list_path = DATA_ROOT / 'test_error_list.json'
    with open(error_list_path) as err_data:
        error_list = json.load(err_data)
    test_dict = {'info': {'header': {'dicom': {
        'Modality': 'NM',
        'ImageType': ['SCREEN SAVE'],
        'Units': 'MLML'}
    }}}
    ret_error_dicts = run.get_container_errors(error_list, test_dict, dict())
    ret_error_msg_list = set([error.get('error') for error in ret_error_dicts])
    exp_msg_list = set([error.get('error_message') for error in error_list])
    assert ret_error_msg_list == exp_msg_list


def test_fix_all():
    error_list_path = DATA_ROOT / 'test_error_list.json'
    with open(error_list_path) as err_data:
        error_list = json.load(err_data)
    test_dict = {'info': {'header': {'dicom': {
        'Modality': 'MR',
        'ImageType': ['NORM'],
        'StudyDate': 'defined'}
    }}}
    ret_error_dicts = run.get_container_errors(error_list, test_dict, dict())
    for item in ret_error_dicts:
        assert item.get('resolved')
