import argparse
import flywheel
import logging

log = logging.getLogger(__name__)
ERROR_LOG_SUFFIX = 'error.log.json'


def has_error_log(container):
    """Checks if the container has a file that ends with the error log suffix

    Args:
        container (flywheel.Container): A flywheel container

    Returns:
        bool: Whether or not container has an error log
    """
    for file_ in container.files:
        if file_.name.endswith(ERROR_LOG_SUFFIX):
            return True
    return False


def get_children(container):
    """Returns children of a container, only returns subjects for projects,
        sessions for subjects, and acquisitions for sessions

    Args:
        container (flywheel.Container): flywheel container

    Returns:
        generator|list: iterable of child containers
    """
    if container.container_type == 'project':
        return container.subjects.iter()
    elif container.container_type == 'subject':
        return container.sessions.iter()
    elif container.container_type == 'session':
        return container.acquisitions.iter()
    else:
        return []


def retag_container(container):
    """Adds a tag to a container if the tag is not already there and recursively
        adds tags to the container's children

    Args:
        container (flywheel.Container): The container to add the tag to

    Returns:
        int: Number of tags added
    """
    tags_added = 0
    log.debug('Checking to add tag to %s', container.label)
    if has_error_log(container):
        log.debug('Adding tag to %s', container.label)
        try:
            container.add_tag('error')
            tags_added += 1
        except flywheel.ApiException as e:
            if e.status == 409:
                log.debug('%s %s(%s) already tagged', container.container_type,
                          container.label, container.id)
            else:
                log.error(e, exc_info=True)
    for child in get_children(container):
        tags_added += retag_container(child)

    return tags_added


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Re applies error tags')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='log debug statements')
    parser.add_argument('--api-key', help='Provide apikey instead of cli login')
    parser.add_argument('project_path', help='Resolver path of project to upload to')
    parser.add_argument('--project-id', help='If multiple projects of the same'
                                             + ' name, specify id')

    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        log.setLevel('DEBUG')

    # Create client with api key provided or cli login
    if args.api_key:
        client = flywheel.Client(args.api_key)
    else:
        client = flywheel.Client()

    # Retrieve the project
    if args.project_id:
        project = client.get(args.project_id)
    else:
        project = client.lookup(args.project_path)

    log.info('Adding tags to project %s on site %s', project.label,
             client.get_config().site.api_url)

    tags_added = retag_container(project)
    log.info('Added %d tags', tags_added)

