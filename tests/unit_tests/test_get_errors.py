import pytest
import mock
import run


def test_container_errors_all_true():
    with mock.patch('run.validate', return_value=True):
        errors = run.get_container_errors([{}], {}, {})

    assert len(errors) == 1
    assert errors[0].get('resolved') is True
    assert errors[0].get('error') is None


def test_container_errors_all_error():
    with mock.patch('run.validate', return_value='Oh no!'):
        errors = run.get_container_errors([{}], {}, {})

    assert len(errors) == 1
    assert errors[0].get('resolved') is False
    assert errors[0].get('error') is 'Oh no!'


def test_container_errors_multiple_error():
    with mock.patch('run.validate', side_effect=[True, 'Oh no!']):
        errors = run.get_container_errors([{}, {}], {}, {})

    assert len(errors) == 2
    assert errors[0].get('resolved') is True
    assert errors[0].get('error') is None
    assert errors[1].get('resolved') is False
    assert errors[1].get('error') is 'Oh no!'

