import pytest
import mock
import run


def test_validate_required_exists_valid():
    error = {
        'revalidate': True,
        'schema': {
            'type': 'string',
            'required': True
        },
        'item': 'label'
    }
    container = {'label': 'STRING'}

    error_status = run.validate(container, error)
    assert error_status is True


def test_validate_required_exists_invalid():
    error = {
        'revalidate': True,
        'schema': {
            'type': 'string',
            'required': True
        },
        'item': 'label'
    }
    container = {'label': 1}

    error_status = run.validate(container, error)
    assert error_status == '1 is not of type \'string\''


def test_validate_required_does_not_exist():
    error = {
        'revalidate': True,
        'schema': {
            'type': 'string',
            'required': True
        },
        'item': 'label'
    }
    container = {}

    error_status = run.validate(container, error)
    assert error_status == '\'label\' is required'


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
    assert error_status is True


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
    assert error_status == '1 is not of type \'string\''


def test_validate_does_not_exists():
    error = {
        'revalidate': True,
        'schema': {
            'type': 'string'
        },
        'item': 'label'
    }
    container = {}

    error_status = run.validate(container, error)
    assert error_status is True


def test_not_revalidate():
    error = {
        'revalidate': False,
    }
    container = {}

    error_status = run.validate(container, error)
    assert error_status == 'Skipping revalidation'


def test_not_revalidate_message():
    error = {
        'revalidate': False,
        'error_message': 'Not enough images'
    }
    container ={}

    error_status = run.validate(container, error)
    assert error_status == 'Not enough images'

