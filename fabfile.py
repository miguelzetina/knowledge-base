# -*- coding: utf-8 -*-
from fabric.api import cd, env, require, run, task
from fabric.colors import green, white
from fabric.context_managers import contextmanager, prefix, shell_env
from fabric.operations import put
from fabric.utils import puts

from fabutils import arguments, join, options
from fabutils.context import cmd_msg
from fabutils.env import set_env_from_json_file
from fabutils.tasks import ulocal, ursync_project, urun
from fabutils.text import SUCCESS_ART


@contextmanager
def virtualenv():
    """Activate virtualenv.

    Activates the virtualenv in which the commands shall be run.
    """
    require('site_dir', 'django_settings')

    with cd(env.site_dir):
        with shell_env(DJANGO_SETTINGS_MODULE=env.django_settings):
            yield


@task
def environment(env_name):
    """Creates environment.

    Creates a dynamic environment based on the contents of the given
    environments_file.

    Args:
        env_name(str): Name environment.
    """
    if env_name == 'vagrant':
        result = ulocal('vagrant ssh-config | grep IdentityFile', capture=True)
        env.key_filename = result.split()[1].replace('"', '')

    set_env_from_json_file('environments.json', env_name)


@task
def startapp(app_name):
    """Create new app

    Create a new app inside the Django project.

    Args:
        app_name(str): Name of new app inside project.

    Usage:
        >>> fab environment:vagrant start_app:'app_name'.
    """
    with virtualenv():
        run(join('python manage.py startapp', app_name))


@task
def load_mandatory_dummy_data(*args):
    """
    Loads the dummy data for developing.
    """


@task
def load_dummy_data(*args):
    """
    Loads the dummy data for developing.
    """
    loaddata(
        'areas.json',
        'categories.json',
        'subjects.json',
        'dummy_superuser.json',
        'posts.json',
    )


@task
def createsuperuser():
    """Create superuser.

    Create a superuser to use in the Django application.

    Usage:
        >>> fab environment:vagrant createsuperuser.
    """
    with virtualenv():
        run('python manage.py createsuperuser')


@task
def createdb():
    """New database.

    Creates a new database instance with utf-8 encoding for the project.

    Usage:
        >>>fab environment:vagrant createdb.
    """
    urun('createdb knowledge_base -l en_US.UTF-8 -E UTF8 -T template0')


@task
def resetdb():
    """Restore database.

    Reset the project's database by dropping an creating it again.

    Usage:
        >>>fab environment:vagrant resetdb.
    """
    urun('dropdb knowledge_base')
    createdb()
    migrate()
    load_dummy_data()


@task
def bootstrap():
    """Builds the environment to start the project.

    Create database, apply migrations and collect the static files.

    Usage:
        >>>fab environment:vagrant bootstrap.
    """
    # Build the DB schema and collect the static files.
    createdb()
    migrate()
    load_dummy_data()
    collectstatic()


@task
def loaddata(*args):
    """Loads the given data fixtures into the project's database.

    Args:
        args(str): Name fixture.

    Usage:
        >>>fab environment:vagrant loaddata:'fixture'.
    """
    with virtualenv():
        run(join('python manage.py loaddata', arguments(*args)))


@task
def makemigrations(*args, **kwargs):
    """Creates the new migrations based on the project's models changes.

    Creating new migrations based on the changes you have made to your models.

    Args:
        args (Optional[str]): Create migration for app_name.

    Example:
        fab environment:vagrant makemigrations.
    """
    with virtualenv():
        run(join('python manage.py makemigrations',
                 options(**kwargs), arguments(*args)))


@task
def migrate(*args, **kwargs):
    """Apply migrations.

    Syncs the DB and applies the available migrations.

    Args:
        args (Optional[str]): Specified apps has its migrations.
        kwargs (Optional[str]): Brings the database schema to state where the
                                named migration is applied (migrate_name).

    Example:
        >>>fab environment:vagrant migrate.
    """
    with virtualenv():
        run(join('python manage.py migrate',
                 options(**kwargs), arguments(*args)))


@task
def collectstatic():
    """Collects the static files.

    Usage:
        >>> fab environment:vagrant collectstatic.
    """
    with virtualenv():
        run('python manage.py collectstatic --noinput')


@task
def runserver():
    """Run project.

    Starts the development server inside the Vagrant VM.

    Usage:
        >>>fab environment:vagrant runserver.
    """
    with virtualenv():
        run('python manage.py runserver_plus')


@contextmanager
def node():
    """
    Activates the node version in which the commands shall be run.
    """

    with cd(env.site_dir):
        with prefix('nvm use stable'), shell_env(CI='true'):
            yield


@task
def bower_install(*args, **kwargs):
    """
    Installs frontend dependencies with bower.
    """
    with node():
        run(join('bower install',
                 options(**kwargs), arguments(*args)))


@task
def npm_install():
    """
    Installs the nodejs dependencies defined in package.json
    """
    with node():
        run('npm install')


@task
def deploy(git_ref, upgrade=False):
    """Deploy project.

    Deploy the code of the given git reference to the previously selected
    environment.

    Args:
        upgrade(Optional[bool]):
            Pass ``upgrade=True`` to upgrade the versions of the already
            installed project requirements (with pip)
        git_ref(str): name branch you make deploy.

    Example:
        >>>fab environment:vagrant deploy:devel.
    """
    require('hosts', 'user', 'group', 'site_dir', 'django_settings')

    # Retrives git reference metadata and creates a temp directory with the
    # contents resulting of applying a ``git archive`` command.
    message = white('Creating git archive from {0}'.format(git_ref), bold=True)
    with cmd_msg(message):
        repo = ulocal(
            'basename `git rev-parse --show-toplevel`', capture=True)
        commit = ulocal(
            'git rev-parse --short {0}'.format(git_ref), capture=True)
        branch = ulocal(
            'git rev-parse --abbrev-ref HEAD', capture=True)

        tmp_dir = '/tmp/blob-{0}-{1}/'.format(repo, commit)

        ulocal('rm -fr {0}'.format(tmp_dir))
        ulocal('mkdir {0}'.format(tmp_dir))
        ulocal('git archive {0} ./src | tar -xC {1} --strip 1'.format(
            commit, tmp_dir))

    # Uploads the code of the temp directory to the host with rsync telling
    # that it must delete old files in the server, upload deltas by checking
    # file checksums recursivelly in a zipped way; changing the file
    # permissions to allow read, write and execution to the owner, read and
    # execution to the group and no permissions for any other user.
    with cmd_msg(white('Uploading code to server...', bold=True)):
        ursync_project(
            local_dir=tmp_dir,
            remote_dir=env.site_dir,
            delete=True,
            default_opts='-chrtvzP',
            extra_opts='--chmod=750',
            exclude=["*.pyc", "env/", "cover/"]
        )

    # Performs the deployment task, i.e. Install/upgrade project
    # requirements, syncronize and migrate the database changes, collect
    # static files, reload the webserver, etc.
    message = white('Running deployment tasks', bold=True)
    with cmd_msg(message, grouped=True):
        with virtualenv():

            message = white('Installing Python requirements with pip')
            with cmd_msg(message, spaces=2):
                run('pip install -{0}r ./requirements/production.txt'.format(
                    'U' if upgrade else ''))

            message = white('Migrating database')
            with cmd_msg(message, spaces=2):
                run('python manage.py migrate --noinput')

            message = 'Installing node modules'
            with cmd_msg(message, spaces=2):
                npm_install()

            message = 'Installing bower components'
            with cmd_msg(message, spaces=2):
                bower_install()

            message = white('Collecting static files')
            with cmd_msg(message, spaces=2):
                run('python manage.py collectstatic --noinput')

            message = white('Setting file permissions')
            with cmd_msg(message, spaces=2):
                run('chgrp -R {0} .'.format(env.group))
                run('chgrp -R {0} ../media'.format(env.group))

            message = white('Restarting webserver')
            with cmd_msg(message, spaces=2):
                run('touch ../reload')

            message = white('Registering deployment')
            with cmd_msg(message, spaces=2):
                register_deployment(commit, branch)

    # Clean the temporary snapshot files that was just deployed to the host
    message = white('Cleaning up...', bold=True)
    with cmd_msg(message):
        ulocal('rm -fr {0}'.format(tmp_dir))

    puts(green(SUCCESS_ART), show_prefix=False)
    puts(white('Code from {0} was succesfully deployed to host {1}'.format(
        git_ref, ', '.join(env.hosts)), bold=True), show_prefix=False)


@task
def register_deployment(commit, branch):
    """Register deployment.

    Register the current deployment at Opbeat with given commit and branch.

    Args:
        commit(str): This is last commit project.
        branch(str): Name branch.
    """
    with virtualenv():
        run(
            'curl https://intake.opbeat.com/api/v1/'
            'organizations/$OPBEAT_ORGANIZATION_ID/'
            'apps/$OPBEAT_APP_ID/releases/ \
            -H "Authorization: Bearer $OPBEAT_SECRET_TOKEN" \
            -d rev={commit} \
            -d branch={branch} \
            -d status=completed'
            .format(
                commit=commit, branch=branch
            )
        )


@task
def inspectdb(filename=""):
    """Inspection database.

    Allows the inspection of legacy databases inside Django projects.

    Args:
        filename(str): Name output file.

    Usage:
        >>> fab environment:vagrant inspectdb
        Print the models needed to work with the database

        >>> fab environment:vagrant inspectdb:'filename'
        Use 'filename' as the output file.
    """
    with virtualenv():
        if(filename == ""):
            run('python manage.py inspectdb')
        else:
            run(join('python manage.py inspectdb > ', filename))


# Haystack index tasks
@task
def rebuild_index():
    """
    rebuilds index for haystack search_indexes.
    """
    with virtualenv():
        run('python manage.py rebuild_index --noinput')


# Solr tasks
@task
def run_solr():
    """
    Starts the Sorl demo search engine.
    """
    update_solr_schema()
    require('solr_dir')
    with cd(env.solr_dir):
        run('java -jar start.jar')


@task
def update_solr_schema():
    """
    Replaces project schema file into local solr.
    """
    require('solr_dir', 'site_dir')
    command = (
        'cp {}templates/search_configuration/solr.xml '
        '{}solr/collection1/conf/schema.xml'
    ).format(
        env.site_dir,
        env.solr_dir
    )
    run(command)


@task
def replace_solr_schema(core):
    """
    Replaces solr schema for the given environment.
    example:
    - fab environment:solr replace_solr_schema:staging
    - fab environment:solr replace_solr_schema:production
    """
    require('schema_remote_path', "schema_local_path")
    put(
        env.schema_local_path,
        env.schema_remote_path[core]
    )
    run('sudo systemctl restart solr')


@task
def dropdb():
    """Drop database.

    Drop database without create it again

    Usage:
        >>>fab environment:vagrant dropdb.
    """
    urun('dropdb knowledge_base')


