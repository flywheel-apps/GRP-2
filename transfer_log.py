import csv
import xlrd
import utils
import os


def create_missing_session_error(session_key):
    return {
        'error': 'session {}-{} missing from flywheel'.format(session_key[0], session_key[1]),
        'path': None,
        'type': 'session',
        'resolved': False,
        'label': None,
        '_id': None
    }


def create_unexpected_session_error(session, client):
    return {
        'error': 'session in flywheel not present in transfer log',
        'path': utils.get_resolver_path(client, session),
        'type': 'session',
        'resolved': False,
        'label': session.label,
        '_id': session.id
    }

def simplify(timestamp):
    """Returns the datetime as a formatted string"""
    return timestamp.strftime("%b %d, %Y")


def key(session):
    """Returns a tuple to be used as keys from a session"""
    return (
        session.subject.code,
        session.label,
        "MR - {}".format(simplify(session.timestamp))
    )


def key_from_log(session_log):
    """Returns a key as above from a transfer log entry"""
    return (
        session_log['Subject'],
        session_log['Timepoint'],
        session_log['Modality - Exam Date']
    )


def validate_transfer_log(client, project, transfer_log_path):
    """Main function to be called by the run.py

    Args:
        client (Client): A flywheel sdk client
        project (Project): Flywheel project object
        transfer_log_path (str): Path to transfer_log

    Returns:
        list: a list of error report entries
    """
    transfer_log = read_transfer_log(transfer_log_path)
    missing_sessions_keys, unexpected_sessions_dict = validate_project_against_transfer_log(
        project,
        transfer_log
    )

    errors = []

    for key in missing_sessions_keys:
        errors.append(create_missing_session_error(key))
    for key, session in unexpected_sessions_dict.items():
        errors.append(create_unexpected_session_error(session, client))

    return errors


def validate_project_against_transfer_log(project, transfer_log):
    """Ensures that a session that matches each row of the transfer log exists
    in the project and warns of any sessions that are not reflected in the
    transfer log

    Args:
        project (Project): Flywheel project object
        transfer_log (list): List of dictionaries, each dictionary is a sesson

    Returns:
        tuple: A list of missing session keys and a dictionary of unexpected
            session keys to the corresponding session
    """
    sessions = {key(session): session for session in project.sessions()}
    session_keys = [key_from_log(session_log) for session_log in transfer_log]

    missing_sessions = []

    for session_key in session_keys:
        if not sessions.get(session_key):
            missing_sessions.append(session_key)
        else:
            sessions.pop(session_key)

    return missing_sessions, sessions


def read_transfer_log(transfer_log_path):
    """Reads the contents of the transfer log xlsx or csv and returns each
    row as a dictionary

    Args:
        transfer_log_path (str): Path to transfer_log

    Returns:
        list: A list of rows as dictionaries
    """
    extension = os.path.splitext(transfer_log_path)[1]
    if extension == '.xlsx':
        wb = xlrd.open_workbook(transfer_log_path)
        sh = wb.sheet_by_index(0)
        transfer_log = []
        keys = None
        for row in sh.get_rows():
            if keys is None:
                keys = [cell.value for cell in row]
            else:
                transfer_log.append({
                    keys[i]: row[i].value for
                    i in range(len(keys))
                })
    elif extension == '.csv':
        with open(transfer_log_path, 'r') as fp:
            csv_reader = csv.DictReader(fp)
            transfer_log = [row for row in csv_reader]
    else:
        raise Exception('Invalid transfer log filetype %s', extension)
    return transfer_log

