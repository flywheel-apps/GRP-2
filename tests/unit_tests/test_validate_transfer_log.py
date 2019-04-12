import datetime
import pytest
import mock

import run

DATE = datetime.datetime.now()


class MockProject:

    def __init__(self, session_count, session_per_subject=1):
        self.session_count = session_count
        self.session_per_subject = session_per_subject

    def sessions(self):
        for session_number in range(self.session_count):
            yield mock.MagicMock(label=str(session_number), timestamp=DATE,
                                 subject=mock.MagicMock(code=str(session_number//self.session_per_subject)))


def format_transfer_log(subject_code, session_label):
    return {
        "Subject": subject_code,
        "Timepoint": session_label,
        "Modality - Exam Date": "MR - {}".format(DATE.strftime("%b %d, %Y"))
    }


def test_validate_project():
    project = MockProject(1)
    transfer_log = [format_transfer_log('0', '0')]
    missing_sessions, unexpected_sessions =  \
        run.validate_project_against_transfer_log(project, transfer_log)

    assert len(missing_sessions) == 0
    assert len(unexpected_sessions) == 0


def test_validate_project_with_missing_sessions():
    project = MockProject(1)
    transfer_log = [
        format_transfer_log('0', '0'),
        format_transfer_log('1', '1')
    ]
    missing_sessions, unexpected_sessions =  \
        run.validate_project_against_transfer_log(project, transfer_log)

    assert len(missing_sessions) == 1
    assert set(missing_sessions[0]) == set(transfer_log[1].values())
    assert len(unexpected_sessions) == 0


def test_validate_project_with_unexpected_sessions():
    project = MockProject(2)
    transfer_log = [format_transfer_log('0','0')]
    missing_sessions, unexpected_sessions =  \
        run.validate_project_against_transfer_log(project, transfer_log)

    assert len(missing_sessions) == 0
    assert len(unexpected_sessions) == 1
    assert set(unexpected_sessions[0]) == set(format_transfer_log('1','1').values())

