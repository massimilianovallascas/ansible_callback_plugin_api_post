from __future__ import (absolute_import, division, print_function)

__metaclass__ = type

import getpass
import json
import re
import socket
import uuid

from ansible.executor.task_result import TaskResult
from ansible.module_utils._text import to_text
from ansible.module_utils.urls import open_url
from ansible.parsing.ajson import AnsibleJSONEncoder
from ansible.plugins.callback import CallbackBase

from base64 import b64encode
from datetime import datetime

from os.path import basename

DOCUMENTATION = '''
    author: Massimiliano Vallascas
    callback: api
    callback_type: stdout
    short_description: send playbook output to an external API
    version_added: 2.9
    description:
        - This callback send playbook output to a an external endpoint
    requirements:
        - Access to remote API (if not public)
    options:
        endpoint:
            default: https://localhost
            description: API endpoint
            env:
              - name: CALLBACK_API_ENDPOINT
            ini:
              - section: callback_api
                key: endpoint
            required: True
        username: 
            description: Username to access the API endpoint
            env:
              - name: CALLBACK_API_USERNAME
            ini:
              - section: callback_api
                key: username
            required: True
        password: 
            description: Password to access the API endpoint
            env:
              - name: CALLBACK_API_PASSWORD
            ini:
              - section: callback_api
                key: password
            required: True
        required_variables:
            default: ""
            description: Extra variables to be present so that the POST action will be submitted, if empty default values will be loaded (resource_id,transaction_id)
            env:
              - name: CALLBACK_API_REQUIRED_VARIABLES
            ini:
              - section: callback_api
                key: required_variables
        skip_empty_task_name:
            default: False
            description: If the task doesn't have a name set then the POST action will be skipped
            env:
              - name: CALLBACK_API_SKIP_EMPTY_TASK_NAME
            ini:
              - section: callback_api
                key: skip_empty_task_name
            type: bool
        verbose:
            default: False
            description: Send verbose POST to API endpoint
            env:
              - name: CALLBACK_API_VERBOSE
            ini:
              - section: callback_api
                key: verbose
            type: bool
'''


class CallbackModule(CallbackBase):
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'stdout'
    CALLBACK_NAME = 'api'
    CALLBACK_NEEDS_WHITELIST = False

    def __init__(self):
        self.api = {}
        self.ansible = {
            'host': socket.gethostname(),
            'ip_address': socket.gethostbyname(socket.gethostname()),
            'play': None,
            'play_variable_manager': None,
            'playbook': None,
            'task': None,
            'version': None,
        }
        self.disable = False
        self.framework = {}
        self.session = str(uuid.uuid4())  # uuid.uuid4().hex[:6]
        self.start_datetimes = {}
        self.user = getpass.getuser()

        super(CallbackModule, self).__init__()

    def set_options(self, task_keys=None, var_options=None, direct=None):
        super(CallbackModule, self).set_options(task_keys=task_keys, var_options=var_options, direct=direct)

        self.api = {
            'endpoint': self.get_option('endpoint'),
            'username': self.get_option('username'),
            'password': self.get_option('password'),
            'required_variables': self.get_option('required_variables').split(','),
            'skip_empty_task_name': self.get_option('skip_empty_task_name'),
            'verbose': bool(self.get_option('verbose'),),
            'is_secure': True,
            'token': None,
        }
        self._check_options()

    def _check_options(self):
        if not self.api["endpoint"] or not self.api["username"] or not self.api["password"]:
            self._display.warning('Callback plugin disable, required variables not present. Plase check your configuration')
            self.disabled = True

        pattern = r'(?i)^(http)://'
        if re.match(pattern, self.api['endpoint']):
            self.api['is_secure'] = False
            self._display.warning('Endpoint without TSL, be careful, your data will be sent in plain text')

        pattern = r'(?i)^(http|https)://'
        if not re.match(pattern, self.api['endpoint']):
            self.api['endpoint'] = 'https://' + self.api['endpoint']
            message = 'Endpoint without schema, prepending https://. The new endpoint is {}'.format(
                self.api['endpoint'])
            self._display.warning(message)

        if self.api['username'] is not None and self.api['password'] is not None:
            data = '%s:%s' % (self.api['username'], self.api['password'])
            self.api['token'] = str(b64encode(data.encode("utf-8")), "utf-8")
        else:
            self._display.warning('API plugin expects to send data to public endpoint, no AUTH details provided')

        self.api['required_variables'] = [key for key in self.api['required_variables'] if key]
        if self.api['required_variables']:
            message = "required_variables variable set to `{}`".format(self.api['required_variables'])
            self._display.warning(message)

    def _runtime(self, result):
        runtime = float(0)
        if isinstance(result, TaskResult):
            runtime = (datetime.utcnow() - self.start_datetimes[result._task._uuid]).total_seconds()

        return runtime

    def _set_payload(self, state, result, runtime):
        post_flag = True

        if isinstance(result, TaskResult):
            if result._task_fields['args'].get('_ansible_version'):
                self.ansible['version'] = result._task_fields['args'].get('_ansible_version')

            self.ansible["task_result"] = result
            
            task_name = result._task.name or result._task.action
            task_uuid = result._task._uuid

            if not result._task.name and self.api['skip_empty_task_name']:
                post_flag = False

        data = {
            'post_flag': post_flag,
            'runtime': self._runtime(result),
            'session': self.session,
            'status': state,
            'timestamp': datetime.utcnow(),
            'user': self.user,
        }

        if isinstance(result, TaskResult):
            data['task_name'] = task_name
            data['task_uuid'] = task_uuid

        if self.api['verbose']:
            data['host'] = self.ansible['host']
            data['ip_address'] = self.ansible['ip_address']

        if isinstance(result, TaskResult) and self.api['verbose']:
            data['verbose'] = str(self.ansible['task_result'].__dict__)

        return data

    def _allowed_to_post(self):
        allowed = False
        variables_check = False
        variables_status_list = []

        if len(self.api['required_variables']) > 0:
            if self.ansible['play_variable_manager']:
                for key in self.api['required_variables']:
                    if key in self.ansible['play_variable_manager'].extra_vars:
                        variables_status_list.append(1)

                if sum(variables_status_list) == len(self.api['required_variables']):
                    variables_check = True
        else:
            variables_check = True

        if not self.ansible['play_variable_manager'] or \
                self.ansible['play_variable_manager'] and len(self.api['required_variables']) == 0 or \
                self.ansible['play_variable_manager'] and variables_check:
            allowed = True

        return allowed

    def post_data(self, state, result, runtime):
        if self._allowed_to_post():
            data = self._set_payload(state, result, runtime)

            if data['post_flag']:
                del(data['post_flag'])
                self._post_to_endpoint(data)
            else:
                self._display.warning('Task with empty name, POST to API skipped')
        else:
            self._display.warning('Post to API disabled')

    def _post_to_endpoint(self, data):
        json_data = json.dumps(data, cls=AnsibleJSONEncoder, sort_keys=True)
        json_data = '{"event":' + json_data + "}"

        headers = {'Content-Type': 'application/json'}

        if self.api['token']:
            headers['Authorization'] = 'Bearer %s' % self.api['token']

        message = "Posting to endpoint `{}`, data: `{}`, headers: `{}`".format(self.api['endpoint'], json_data, headers)
        self._display.debug(message)
        try:
            response = open_url(self.api['endpoint'], json_data, headers, method='POST')
            return response.read()
        except Exception as ex:
            self._display.warning('Could not submit message to the API: %s' % to_text(ex))

    def v2_playbook_on_start(self, playbook):
        self.ansible['playbook'] = basename(playbook._file_name)
        self.post_data('PLAYBOOK: {}'.format(self.ansible['playbook']), '', '')

    def v2_playbook_on_play_start(self, play):
        self.ansible['play'] = play
        self.ansible['play_variable_manager'] = play.get_variable_manager()
        self._display.warning('Extra vars: %s' % to_text(self.ansible['play_variable_manager'].extra_vars))
        self.post_data('PLAY: {}'.format(self.ansible['play']), '', '')

    def v2_playbook_on_task_start(self, task, is_conditional):
        self.start_datetimes[task._uuid] = datetime.utcnow()

    def v2_playbook_on_include(self, included_file):
        self.post_data('Include file: {}'.format(included_file), '', '')

    def v2_runner_on_failed(self, result, ignore_errors=False):
        self.post_data('Failed', result, self._runtime(result))

    def v2_runner_on_ok(self, result):
        self.post_data('Ok', result, self._runtime(result))

    def v2_runner_on_skipped(self, result):
        self.post_data('Skipped', result, self._runtime(result))

    def v2_runner_on_unreachable(self, result):
        self.post_data('Unreachable', result, self._runtime(result))

    def v2_runner_on_async_failed(self, result):
        self.post_data('Async failed', result, self._runtime(result))

    def playbook_on_import_for_host(self, host, imported_file):
        self.post_data('Imported file: {}'.format(imported_file), '', '')

    def playbook_on_not_import_for_host(self, host, missing_file):
        self.post_data('Not imported file: {}'.format(missing_file), '', '')
