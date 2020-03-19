from run import get_error_origin_file_dict, ERROR_LOG_FILENAME_SUFFIX


def test_get_error_origin_file_dict():

    # Test existing file
    test_file_name = 'exists.dicom.zip'
    test_error_log_name = '.'.join([test_file_name, ERROR_LOG_FILENAME_SUFFIX])
    acq_dict = {'files': [{'name': test_file_name}, {'name': test_error_log_name}]}
    result = get_error_origin_file_dict(acq_dict, test_error_log_name)
    assert result.get('name') == test_file_name

    # Test missing file
    test_error_log_name = 'does_not_' + test_error_log_name
    result = get_error_origin_file_dict(acq_dict, test_error_log_name)
    assert result is None

    # Test empty file list
    acq_dict = {'files': []}
    result = get_error_origin_file_dict(acq_dict, test_error_log_name)
    assert result is None
