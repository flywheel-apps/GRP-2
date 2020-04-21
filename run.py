#!/usr/bin/env python

import csv
import datetime
import copy
import flywheel
import json
import logging
import jsonschema

ERROR_LOG_FILENAME_SUFFIX = 'error.log.json'
CSV_HEADERS = [
    'path',
    'url',
    'error',
    'resolved',
    '_id',
    'type'
]


log = logging.getLogger('grp-2')
log.setLevel('INFO')


def get_resolver_path(client, container):
    """Generates the resolveer path for a container

    Args:
        client (Client): Flywheel Api client
        container (Container): A flywheel container

    Returns:
        str: A human-readable resolver path that can be used to find the
            container
    """
    resolver_path = []
    for parent_type in ['group', 'project', 'subject', 'session']:
        parent_id = container.parents.get(parent_type)
        if parent_id:
            if parent_type == 'group':
                path_part = client.get(parent_id).id
            else:
                path_part = client.get(parent_id).label
            resolver_path.append(path_part)
        else:
            break
    resolver_path.append(container.label)
    return '/'.join(resolver_path)


def get_uri(client, container):
    """Generates the uri for a container. If its a session or acquisition,
    the uri will be to the session on the project session tab. Otherwise, it
    will be to the project description page.

    Args:
        client (Client): Flywheel Api client
        container (Container): A flywheel container

    Returns:
        str: A uri that can be used to find the
            container
    """
    first = ':'.join(client.get_config().site.api_url.split(':')[:-1])
    uri = None
    if container.container_type == 'project':
        uri = first + '/#/projects/{}'.format(container.id)
    elif container.container_type == 'session':
        uri = first + '/#/projects/{}/sessions/{}?tab=data'.format(container.project, container.id)
    elif container.container_type == 'acquisition':
        uri = first + '/#/projects/{}/sessions/{}?tab=data'.format(container.parents.project, container.parents.session)
    else:
        uri = first + '/#/projects/{}'.format(container.parents.project)
    return uri


def add_additional_info(error_containers, client):
    """Adds additional info to container entries such as resolver path and uri

    Args:
        error_containers (list): list of container dictionaries
        client (Client): Flywheel Api client
    """
    for error_container in error_containers:
        container = client.get(error_container['_id'])
        error_container['path'] = get_resolver_path(client, container)
        error_container['url'] = get_uri(client, container)


def collect_containers(finder, container_type, collect_acquisitions=False,
                       skip_sessions=False):
    """Iterates over finder for containers with tags=error filter, and returns
    a list of dictionaries with the container id and type

    Args:
        finder (Finder): A flywheel sdk finder
        container_type (str): The container type returned by the finder
        collect_acquisitions (bool): Optional flag to iterate over the
            acquisitions
        skip_sessions (bool): Optional flag to skip collecting sessions if only
            collecting acquisitions

    Returns:
        list: A list of dictionaries with the container id and type set
    """
    error_containers = []
    log.debug('Inside collect function, collect acqs %s', collect_acquisitions)
    log.debug('Container type %s', container_type)
    for container in finder.find('tags=error'):
        log.debug('Checking container %s', container.label)
        if container_type != 'session' or not skip_sessions:
            error_containers.append({
                '_id': container.id,
                'type': container_type
            })
    if collect_acquisitions:
        for session in finder.find():
            log.debug('Collecting acquisitions for session %s', session.label)
            for acquisition in session.acquisitions.find('tags=error'):
                error_containers.append({
                    '_id': acquisition.id,
                    'type': 'acquisition'
                })
    return error_containers


def find_error_containers(container_type, parent):
    """Given a parent and a container type, the function will return a list
    of all containers of the given container_type that have the tag error

    Args:
        container_type (str): Must be 'all', 'subject', 'session', or
            'acquisition'
        parent (ContainerOutput): The parent container, can be a project,
            subject, or session, and this restrict what the container type can
            be

    Returns:
        list: A list of containers (_id and type) that are tagged as
            error
    """
    error_containers = []
    if container_type not in ['all', 'subject', 'session', 'acquisition']:
        raise ValueError('Container type {} not valid'.format(container_type))

    # If collecting all container types under the project or just subjects
    if (
        ( container_type == 'all' and parent.container_type == 'project')  or
        ( container_type == 'subject')
    ):
        if parent.container_type != 'project':
            # If the parent type isn't a project, the user selected subject as
            # as the container_type but didn't run the job on a project
            raise ValueError('Cannot find subjects of a parent of type %s',
                             parent.container_type)

        error_containers += collect_containers(parent.subjects, 'subject')

    # If collecting all container types under a project or a subject; or just
    # the sessions under a container, or acquisitions
    # NOTE: This is because we have to loop through the sessions to get through
    # all acquisitions of a project or subject
    if (
        ( container_type in ['all', 'acquisition'] and parent.container_type in ['project', 'subject'])  or
        ( container_type == 'session')
    ):
        if parent.container_type not in ['project', 'subject'] and container_type == 'session':
            # If the parent type isn't a container above a session, but session
            # was specifically chosen as container type raise and exception
            raise ValueError('Cannot find sessions of a parent of type %s',
                             parent.container_type)

        collect_acquisitions = container_type == 'all' or container_type == 'acquisition'
        log.debug('Collecting acquisitions? %s', collect_acquisitions)
        skip_sessions = container_type == 'acquisition'
        log.debug('Skip sessions? %s', skip_sessions)
        error_containers += collect_containers(parent.sessions, 'session',
                                               collect_acquisitions=collect_acquisitions,
                                               skip_sessions=skip_sessions)

    # If the parent type is a session, loop through the acquisitions
    if parent.container_type == 'session':
        if container_type not in ['all', 'acquisition']:
            # User should not choose a session to run if container_type is not
            # all or acquisition
            raise ValueError('Invalid container type {} for children of session'.format(container_type))
        error_containers += collect_containers(parent.acquisitions, 'acquisition')

    return error_containers


def create_output_file(container_label, error_containers, file_type,
                       gear_context, timestamp, output_filename=None):
    """Creates the output file from a set of error containers, the file type
    is determined from the config value

    Args:
        container_label (str): The label of root container
        error_containers (list): list of containers that were tagged
        file_type (str): The file type to format the output into
        gear_context (GearContext): the gear context so that we can write out
            the file
        output_filename (str): and optional file name that can be passed

    Returns:
        str: The filename that was used to write the report as
    """
    file_ext = 'csv' if file_type == 'csv' else 'json'
    output_filename = output_filename or '{}-{}.{}'.format(
        container_label,
        timestamp,
        file_ext
    )
    with gear_context.open_output(output_filename, 'w') as output_file:
        if file_type == 'json':
            json.dump(error_containers, output_file)
        elif file_type == 'csv':
            csv_dict_writer = csv.DictWriter(output_file,
                                             fieldnames=CSV_HEADERS)
            csv_dict_writer.writeheader()
            for container in error_containers:
                csv_dict_writer.writerow(container)
        else:
            raise Exception('CRITICAL: {} is not a valid file type')
    return output_filename


def dictionary_lookup(field, dictionary):
    """A traverses a dictionary with a period seperated list of fields as a str

    Args:
        field (str): period separated string of fields
        dictionary (dict): the dictionary to lookup

    Returns:
        object: the value stored in the dictionary, None if it was not found
        bool: Whether or not the field was found
    """
    d = dictionary
    if field is None:
        return None, False
    for part in field.split('.'):
        if isinstance(d, dict):
            if part in d:
                d = d[part]
            else:
                return None, False
        elif isinstance(d, list) and part.isdigit():
            if int(part) < len(d):
                d = d[int(part)]
            else:
                return None, False
        else:
            return None, False
    return d, True


def validate(container, error):
    """Wraps jsonschema.validate so that it returns a boolean instead of
    raising an Error

    Args:
        container (dict): The container to validate
        error (dict): An error with schema and item fields

    Returns:
        list: list of validation error messages (empty if none)
    """
    if not error.get('revalidate'):
        return [error.get('error_message', 'Skipping revalidation')]
    schema = error.get('schema', {})
    if not schema:
        log.error('Cannot re-validate error for %s - schema key is missing!',
                  container.get('name', container.get('label', 'NA')))
        log.error('For best results, please run the latest version of GRP-3')
        return [error.get('error_message', 'Error schema is missing, cannot re-validate.')]
    item = error.get('item')
    value, found_value = dictionary_lookup(item, container)
    if found_value is False:

        err_string = 'Could not find {} on file: {}. Please confirm metadata are not missing.'.format(
            item,
            container.get('name', container.get('label', 'NA'))
        )
        log.error(err_string)
        log.error(error)
        return [error.get('error_msg', err_string)]

    validation_output = get_schema_errors(value, schema)

    return validation_output


def get_schema_errors(value, schema):
    """
    Validate the value against the schema provided
    Args:
        value: the value against which to validate the schema
        schema (dict): jsonschema object against which to validate the value

    Returns:
        list: a list of validation errors
    """
    # Initialize json schema validator
    validator = jsonschema.Draft7Validator(schema)
    # Initialize list object for storing validation error messages
    msg_list = list()
    for error in sorted(validator.iter_errors(value), key=str):
        msg_list.append(error.message)
    return msg_list


def get_container_errors(error_log, file_dict, container_dictionary):
    """Uses parameters given in the error log to validate the container

    Args:
        error_log (list): list of error objects
        file_dict (dict): The file metadata to validate
        container_dictionary (dict): The error container dictionary

    Returns:
        list: A list of error dictionaries
    """
    error_dictionaries = list()
    err_msg_list = list()
    for error in error_log:
        error_dictionary = copy.deepcopy(container_dictionary)
        error_status = validate(file_dict, error)
        if error_status == list():
            error_dictionary['resolved'] = True
            error_dictionaries.append(error_dictionary)
        else:
            for error_msg in error_status:
                tmp_error_dictionary = copy.deepcopy(error_dictionary)
                if error_msg not in err_msg_list:
                    err_msg_list.append(error_msg)
                    tmp_error_dictionary['resolved'] = False
                    tmp_error_dictionary['error'] = error_msg
                    error_dictionaries.append(tmp_error_dictionary)
    return error_dictionaries


def get_error_origin_file_dict(container_dict, error_log_name):
    """
    Finds the file dictionary in container_dict['files'] matching the error_log_name without ERROR_LOG_FILENAME_SUFFIX.
    Returns None if a matching file dictionary is not present.

    :param container_dict: dictionary representing a flywheel container
    :param error_log_name: name of the error log file
    :return: None or dict
    """
    file_dict = None
    file_list = container_dict.get('files', [])
    origin_file_name = error_log_name.rstrip(f'.{ERROR_LOG_FILENAME_SUFFIX}')
    if file_list:
        file_dict = next((file_dict for file_dict in file_list if file_dict['name'] == origin_file_name), None)

    return file_dict


def get_errors(error_containers, client, delete_errors=False):
    """Generate a list of errors of all the containers and set the resolution
    and error message for each, if the error.log file DNE, we create a single
    error for the container without a message and resolved set to True

    Args:
        error_containers (list): list of container dictionaries
        client (Client): An api client
    Returns:
        list: A list of errors (many to one container)
    """
    errors = []
    for container_dictionary in error_containers:
        container = client.get_container(container_dictionary['_id'])
        error_log_filenames = [file_.name for file_ in container.files if
                               file_.name.endswith(ERROR_LOG_FILENAME_SUFFIX)]
        if error_log_filenames:
            for error_log_filename in error_log_filenames:
                origin_file_dict = get_error_origin_file_dict(container.to_dict(), error_log_filename)
                log.critical('Reading file %s on %s %s', error_log_filename, container.container_type, container.id)
                error_log = json.loads(container.read_file(error_log_filename))
                container_errors = get_container_errors(error_log,
                                                        origin_file_dict,
                                                        container_dictionary)

                resolved = all([
                    container_error['resolved'] for
                    container_error in
                    container_errors
                ])
                if resolved and delete_errors:
                    log.info('Deleting {} for {}={}...'.format(
                        error_log_filename,
                        container.container_type,
                        container.id
                    ))
                    container.delete_file(error_log_filename)
                    container.delete_tag('error')
                errors += container_errors
        else:
            # If the error file isn't there, assume it was resolved
            resolved = True
            container.delete_tag('error')
            container_dictionary['resolved'] = True
            errors.append(container_dictionary)
    return errors


def update_analysis_label(parent_type, parent_id, analysis_id, analysis_label,
                          apikey, api_url):
    """Helper function to make a request to the api without the sdk because the
    sdk doesn't support updating analysis labels

    Args:
        parent_type (str): Singularized container type
        parent_id (str): The id of the parent
        analysis_id (str): The id of the analysis
        analysis_label (str): The label that should be set for the analysis
        apikey (str): The api key for the client
        api_url (str): The url for the api

    Returns:
        dict: Api response for the request
    """
    import requests

    url = '{api_url}/{parent_name}/{parent_id}/analyses/{analysis_id}'.format(
        api_url=api_url,
        parent_name=parent_type+'s',
        parent_id=parent_id,
        analysis_id=analysis_id
    )

    headers = {
        'Authorization': 'scitran-user {}'.format(apikey),
        'Content-Type': 'application/json'
    }

    data = json.dumps({
        "label": analysis_label
    })

    raw_response = requests.put(url, headers=headers, data=data)
    return raw_response.json()


def main():
    with flywheel.GearContext() as gear_context:
        gear_context.init_logging()
        log.info(gear_context.config)
        log.info(gear_context.destination)
        container_type = gear_context.config.get('container_type')
        delete_error_logs = gear_context.config.get('delete_error_logs')
        analysis = gear_context.client.get_analysis(
            gear_context.destination['id']
        )
        parent = gear_context.client.get_container(analysis.parent['id'])

        # Get all containers
        # TODO: Should it be based on whether the error.log file exists?
        log.info('Finding containers with errors...')
        error_containers = find_error_containers(container_type, parent)
        log.debug('Found %d containers', len(error_containers))

        # Set the resolve paths
        add_additional_info(error_containers, gear_context.client)

        # Set the status for the containers
        log.info('Resolving status for invalid containers...')
        # TODO: Figure out the validator stuff, maybe have our validation be a
        # pip module?
        errors = get_errors(error_containers, gear_context.client, delete_errors=delete_error_logs)
        error_count = len(errors)

        log.info('Writing error report')
        timestamp = datetime.datetime.utcnow()
        filename = create_output_file(parent.label, errors,
                                      gear_context.config.get('file_type'),
                                      gear_context, timestamp,
                                      gear_context.config.get('filename'))
        log.info('Wrote error report with filename {}'.format(filename))

        # Update analysis label
        analysis_label = 'Metadata Error Report: COUNT={} [{}]'.format(error_count, timestamp)
        log.info('Updating label of analysis={} to {}'.format(analysis.id, analysis_label))

        # TODO: Remove this when the sdk lets me do this
        update_analysis_label(parent.container_type, parent.id, analysis.id,
                              analysis_label,
                              gear_context.client._fw.api_client.configuration.api_key['Authorization'],
                              gear_context.client._fw.api_client.configuration.host)


if __name__ == '__main__':
    main()
