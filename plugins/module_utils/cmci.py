#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright (c) IBM Corporation 2019, 2020
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule, missing_required_lib, env_fallback

import re
import traceback

try:
    import requests
except ImportError:
    requests = None
    REQUESTS_IMP_ERR = traceback.format_exc()

try:
    import xmltodict
except ImportError:
    xmltodict = None
    XMLTODICT_IMP_ERR = traceback.format_exc()

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community',
}

DOCUMENTATION = r"""
---
module: cics_cmci
short_description: Manage CICS and CPSM resources
description:
  - The cics_cmci module could be used to  manage installed and definitional
    CICS and CICSPlex® SM resources on CICS regions.
options:
  cmci_host:
    description:
      - The TCP/IP host name of CMCI connection
    type: str
    required: true
  cmci_port:
    description:
      - The port number for CMCI connection.
    type: str
    required: true
  cmci_user:
    description:
      - The user id to run the CMCI request with.
      - Required when security type is yes.
      - Can also be specified using the environment variable CMCI_USER
    type: str
  cmci_password:
    description:
      - The password of cmci_user to pass to the basic authentication
      - Can also be specified using the environment variable CMCI_PASSWORD
    type: str
  cmci_cert:
    description:
      - Location of the PEM-formatted certificate chain file to be used for
        HTTPS client authentication.
      - Required when security type is certificate.
      - Can also be specified using the environment variable CMCI_CERT
    required: false
    type: str
  cmci_key:
    description:
      - Location of the PEM-formatted file with your private key to be used
        for HTTPS client authentication.
      - Required when security type is certificate.
      - Can also be specified using the environment variable CMCI_KEY
    required: false
    type: str
  security_type:
    description:
      - the authenticate type that remote region requires
    required: true
    type: str
    choices:
      - none
      - basic
      - certificate
    default: none
  context:
    description:
      - If CMCI is installed in a CICSPlex SM environment, context is the
        name of the CICSplex or CMAS associated with the request; for example,
        PLEX1. See the relevant resource table in CICSPlex SM resource tables
        to determine whether to specify a CICSplex or CMAS.
      - If CMCI is installed as a single server (SMSS), context is the
        APPLID of the CICS region associated with the request.
      - The value of context must not contain spaces. Context is not
        case-sensitive.
    type: str
  scope:
    description:
      - Specifies the name of a CICSplex, CICS region group, CICS region, or
        logical scope associated with the query.
      - Scope is a subset of context, and limits the request to particular
        CICS systems or resources.
      - Scope is not mandatory. If scope is absent, the request is limited by
        the value of the context alone.
      - The value of scope must not contain spaces.
      - Scope is not case-sensitive
    type: str
  option:
    description:
      - The definition or operation you want to perform with your CICS or CPSM
        resources
    type: str
    choices:
      - define
      - delete
      - update
      - install
      - query
    default: query
  resource:
    description:
      - The resource that you want to define or operate with
    type: list
    required: true
    suboptions:
      type:
        description:
          - The resource type.
        type: str
        required: true
      attributes:
        description:
          - The resource attributes, refer to the CICSPlex SM resource tables
            in the knowledge center to find the possible attributes.
        type: list
        required: false
      parameters:
        description:
          - The resource parameters,refer to the CICSPlex SM resource tables
            in the knowledge center to get the possible parameters.
        type: list
        required: false
      location:
        description:
          - The location that resource been installed to.
          - This variable only work with option 'install'.
        type: str
        required: false
        choices:
          - BAS
          - CSD
  criteria:
    description:
      - A string containing logical expressions that filters the data 
        returned on the request.
      - The string that makes up the value of the CRITERIA parameter
        follows the same rules as the filter expressions in the CICSPlex
        SM application programming interface.
      - The filter can work with options ``query``, ``update``, ``delete``; 
        otherwise it will be ignored.
      - For more guidance about specifying filter expressions using the
        CICSPlex SM API, see (https://www.ibm.com/support/knowledgecenter
        /SSGMCP_5.4.0/system-programming/cpsm/eyup1a0.html).
    type: str
    required: false
  parameter:
    description:
      - A string of one or more parameters and values of the form
        parameter_name(data_value) that refines the request. The
        rules for specifying these parameters are the same as in
        the CICSPlex SM application programming interface.
      - For more guidance about specifying parameter expressions using the
        CICSPlex SM API, see (https://www.ibm.com/support/knowledgecenter
        /SSGMCP_5.4.0/system-programming/cpsm/eyup1bg.html)
    type: str
    required: false
  record_count:
    description:
      - Only work with 'query' option, otherwise it will be ignored
      - Identifies a subset of records in a results cache starting from the
        first record in the results cache or from the record specified
        by the index parameter.
      - A negative number indicates a count back from the last record; for
        example, -1 means the last record, -2 the last record but one, and so
        on
      - Count must be an integer, a value of zero is not permitted.
    type: int
    required: false
"""

EXAMPLES = r"""
- name: get a localfile in a CICS region
  cics_cmci:
    cmci_host: 'winmvs2c.hursley.ibm.com'
    cmci_port: '10080'
    cmci_user: 'ibmuser'
    cmci_password: '123456'
    context: 'iyk3z0r9'
    option: 'query'
    resource:
      - type: CICSLocalFile
    record_count: 2
    criteria: 'dsname=XIAOPIN* and file=DFH*'

- name: define a bundle in a CICS region
  cics_cmci:
      cmci_host: 'winmvs2c.hursley.ibm.com'
      cmci_port: '10080'
      context: 'iyk3z0r9'
      option: 'define'
      resource:
        - type: CICSDefinitionBundle
          attributes:
            - name: PONGALT
              BUNDLEDIR: /u/ibmuser/bundle/pong/pongbundle_1.0.0
              csdgroup: JVMGRP
          parameters:
            - name: CSD
      record_count: 1

- name: install a bundle in a CICS region
  cics_cmci:
    cmci_host: 'winmvs2c.hursley.ibm.com'
    cmci_port: '10080'
    context: 'iyk3z0r9'
    option: 'install'
    resource:
      - type: CICSDefinitionBundle
        location: CSD
    criteria: 'NAME=PONGALT'
    parameter: 'CSDGROUP(JVMGRP)'

- name: update a bundle definition in a CICS region
  cics_cmci:
    cmci_host: 'winmvs2c.hursley.ibm.com'
    cmci_port: '10080'
    context: 'iyk3z0r9'
    option: 'update'
    resource:
      - type: CICSDefinitionBundle
        attributes:
          - description: 'forget description'
        parameters:
          - name: CSD
    criteria: 'NAME=PONGALT'
    parameter: 'CSDGROUP(JVMGRP)'

- name: install a bundle in a CICS region
  cics_cmci:
    cmci_host: 'winmvs2c.hursley.ibm.com'
    cmci_port: '10080'
    context: 'iyk3z0r9'
    option: 'update'
    resource:
      - type: CICSBundle
        attributes:
          - Enablestatus: disabled
    criteria: 'NAME=PONGALT'

- name: delete a bundle in a CICS region
  cics_cmci:
    cmci_host: 'winmvs2c.hursley.ibm.com'
    cmci_port: '10080'
    security_type: 'yes'
    context: 'iyk3z0r9'
    option: 'delete'
    resource:
      - type: CICSBundle
    criteria: 'NAME=PONGALT'

- name: delete a bundle definition in a CICS region
  cics_cmci:
    cmci_host: 'winmvs2c.hursley.ibm.com'
    cmci_port: '10080'
    context: 'iyk3z0r9'
    option: 'delete'
    resource:
      - type: CICSDefinitionBundle
    criteria: 'NAME=PONGALT'
    parameter: 'CSDGROUP(JVMGRP)'

- name: get a localfile in a CICS region
  cics_cmci:
    cmci_host: 'winmvs2c.hursley.ibm.com'
    cmci_port: '10080'
    cmci_cert: './sec/ansible.pem'
    cmci_key: './sec/ansible.key'
    connection_type: 'certificate'
    context: 'iyk3z0r9'
    option: 'query'
    resource:
      - type: CICSLocalFile
    record_count: 1
    criteria: 'dsname=XIAOPIN* AND file=DFH*'
"""

RETURN = r"""
changed:
    description: True if the state was changed, otherwise False
    returned: always
    type: bool
failed:
    description: True if query_job failed, othewise False
    returned: always
    type: bool
url:
    description: The cmci url that been composed
    returned: always
    type: str
api_response:
    description: Indicate if the cmci request been issued successfully or not
    returned: always
    type: str
response:
    description: The response of cmci request
    returned: success
    type: dict
    sample:
        {   "records": {
                "cicsdefinitionlibrary": {
                    "_keydata": "D7D6D5C74040404000D1E5D4C7D9D74040",
                    "changeagent": "CSDAPI",
                    "changeagrel": "0710",
                    "changetime": "2020-06-16T10:40:50.000000+00:00",
                    "changeusrid": "CICSUSER",
                    "createtime": "2020-06-16T10:40:50.000000+00:00",
                    "critical": "NO",
                    "csdgroup": "JVMGRP",
                    "defver": "0",
                    "desccodepage": "0",
                    "description": "",
                    "dsname01": "XIAOPIN.PONG.LOADLIB",
                    "dsname02": "",
                    "dsname03": "",
                    "dsname04": "",
                    "dsname05": "",
                    "dsname06": "",
                    "dsname07": "",
                    "dsname08": "",
                    "dsname09": "",
                    "dsname10": "",
                    "dsname11": "",
                    "dsname12": "",
                    "dsname13": "",
                    "dsname14": "",
                    "dsname15": "",
                    "dsname16": "",
                    "name": "PONG",
                    "ranking": "50",
                    "status": "ENABLED",
                    "userdata1": "",
                    "userdata2": "",
                    "userdata3": ""
                }
            },
          "resultsummary": {
                "api_response1": "1024",
                "api_response1_alt": "OK",
                "api_response2": "0",
                "api_response2_alt": "",
                "displayed_recordcount": "1",
                "recordcount": "1"
            }
      }

"""


def cmci_main(option):
    module = AnsibleModule(
        argument_spec=dict(
            cmci_host=dict(
                required=True,
                type='str'
            ),
            cmci_port=dict(
                required=True,
                type='str'
            ),
            cmci_user=dict(
                type='str',
                fallback=(env_fallback, ['CMCI_USER'])
            ),
            cmci_password=dict(
                type='str',
                # no_log=True,
                fallback=(env_fallback, ['CMCI_PASSWORD'])
            ),
            cmci_cert=dict(
                type='str',
                # no_log=True,
                fallback=(env_fallback, ['CMCI_CERT'])
            ),
            cmci_key=dict(
                type='str',
                # no_log=True,
                fallback=(env_fallback, ['CMCI_KEY'])
            ),
            security_type=dict(
                type='str',
                default='none',
                choices=['none', 'basic', 'certificate']
            ),
            context=dict(
                required=True,
                type='str'
            ),
            scope=dict(
                type='str'
            ),
            criteria=dict(
                type='str',
                required=False
            ),
            parameter=dict(
                type='str',
                required=False
            ),
            record_count=dict(type='int'),
            resource=dict(
                type='dict',
                required=True,
                options=dict(
                    type=dict(
                        type='str',
                        required=True
                    ),
                    attributes=dict(
                        type='dict',
                        required=False
                    ),
                    parameters=dict(
                        type='list',
                        required=False,
                        elements='dict',
                        options=dict(
                            name=dict(
                                type='str',
                                required=True
                            ),
                            # Value is not required for flag-type parameters like CSD
                            value=dict(
                                type='str'
                            )
                        )
                    ),
                    location=dict(
                        type='str',
                        required=False,
                        choices=['BAS', 'CSD']
                    )
                )
            ),
        )
    )
    result = dict(changed=False)

    if not requests:
        fail_e(module, result, missing_required_lib('requests'), exception=REQUESTS_IMP_ERR)

    if not xmltodict:
        fail_e(module, result, missing_required_lib('encoder'), exception=XMLTODICT_IMP_ERR)

    session, method, url, request_params, body_xml, resource = _handle_params(module, result, option)
    response = _do_request(module, result, session, method, url, request_params, body_xml)
    _handle_response(module, result, response, method, resource)
    module.exit_json(**result)


def _create_body(params, option):
    if option not in ['install', 'update', 'define']:
        return None

    resource = params.get('resource')
    parameters = resource.get('parameters', None)
    attributes = resource.get('attributes', None)

    request = {}
    if option == 'install':
        # TODO: we don't currently validate location is mandatory, so possible it won't be specified,
        #  which we should validate against
        location = params.get('location')
        request['action'] = {'@name': 'INSTALL' if location == 'BAS' else 'CSDINSTALL'}
    elif option == 'update':
        update = {}
        _append_parameters(update, parameters)
        _append_attributes(update, attributes)
        request['update'] = update
    elif option == 'define':
        create = {}
        _append_parameters(create, parameters)
        _append_attributes(create, attributes)
        request['create'] = create
    document = {"request": request}
    return document


def _append_parameters(element, parameters):
    # Parameters are <parameter name="pname" value="pvalue" />
    if parameters:
        ps = []
        for p in parameters:
            np = {'@name': p.get('name')}
            value = p.get('value')
            if value:
                np['@value'] = value
            ps.append(np)
        element['parameter'] = ps


def _append_attributes(element, attributes):
    # Attributes are <attributes name="value" name2="value2"/>
    if attributes:
        # TODO: validate types?
        element['attributes'] = {'@' + key: value for key, value in attributes.items()}


def _validate_module_params(module, result, params):
    r = "^((([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\\.)"
    r += "{3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5]))|((([a-zA-Z0-9]|[a-zA-Z0-9]"
    r += "[a-zA-Z0-9\\-]*[a-zA-Z0-9])\\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\\-]*"
    r += "[A-Za-z0-9]))$"
    regex_ip_or_host = r
    regex_port = "^([0-9]|[1-9]\\d{1,3}|[1-5]\\d{4}|6[0-4]\\d{3}|65[0-4]\\d{2}|"
    regex_port += "655[0-2]\\d|6553[0-5])$"
    regex_context = "^([A-Za-z0-9]{1,8})$"
    regex_scope = "^([A-Za-z0-9]{1,8})$"
    validations = {
        ("cmci_host", regex_ip_or_host, "an IP address or host name."),
        ("cmci_port", regex_port, "a port number 0-65535."),
        (
            "context",
            regex_context,
            "a CPSM context name.  CPSM context names are max 8 characters.  Valid characters are A-Z a-z 0-9."
        ),
        (
            "scope",
            regex_scope,
            "a CPSM scope name.  CPSM scope names are max 8 characters.  Valid characters are A-Z a-z 0-9."
        )
    }

    # TODO: Should probably change this so the validations are lambdas or classes
    for name, regex, message in validations:
        value = str(params.get(name))
        pattern = re.compile(regex)
        if not pattern.fullmatch(value):
            fail(
                module,
                result,
                'Parameter "{0}" with value "{1} was not valid.  Expected {2}'.format(name, value, message)
            )


def _handle_module_params(module, option):
    parameters = {}
    # TODO: Don't know why this is necessary, should remove!
    #  I think this copies everything because it wants to set values like 'method' but module.params is immutable!
    for key, value in module.params.items():
        parameters[key] = value
    method_action_pair = {'define': 'POST', 'install': 'PUT', 'update': 'PUT', 'delete': 'DELETE', 'query': 'GET'}
    for key, value in method_action_pair.items():
        if option == key:
            parameters['method'] = value
    return parameters


def _handle_params(module, result, option):
    params = _handle_module_params(module, option)
    _validate_module_params(module, result, params)
    session = _create_session(module, result, **params)
    url, resource, request_params = _get_url(params, option)
    body = _create_body(params, option)
    # TODO: can this fail?
    # full_document=False suppresses the xml prolog, which CMCI doesn't like
    body_xml = xmltodict.unparse(body, full_document=False) if body else None
    method = params.get('method')

    result_request = {
        'url': url,
        'method': method,
        'body': body_xml
    }

    if request_params:
        result_request['params'] = request_params

    result['request'] = result_request

    return session, method, url, request_params, body_xml, resource


def _handle_response(module, result, response, method, resource):
    # Try and parse the XML response body into a dict
    content_type = response.headers.get('content-type')
    # Content type header may include the encoding.  Just look at the first segment if so
    content_type = content_type.split(';')[0]
    if content_type != 'application/xml':
        fail(module, result, 'CMCI request returned a non application/xml content type: {0}'.format(content_type))

    # Missing content
    if not response.content:
        fail(module, result, 'CMCI response did not contain any data')

    # Fail the task in the event of a CMCI error
    try:
        # TODO: What exception do we actually get from this? Do I actually need to strip namespaces
        namespaces = {
            'http://www.ibm.com/xmlns/prod/CICS/smw2int': None,
            'http://www.w3.org/2001/XMLSchema-instance': None
        }  # namespace information

        response_dict = xmltodict.parse(
            response.content,
            process_namespaces=True,
            namespaces=namespaces,
            force_list=(resource,)  # Make sure we always return a list for the resource node
        )

        # Attached parsed xml to response
        result['response']['body'] = response_dict

        try:
            result_summary = response_dict['response']['resultsummary']
            cpsm_response = result_summary['@api_response1']

            # Non-OK queries fail the module, except if we get NODATA on a query, when there are no records
            if cpsm_response != '1024' and not (method == 'query' and cpsm_response == '1027'):
                cpsm_response_alt = result_summary['@api_response1_alt']
                cpsm_reason = result_summary['@api_response2_alt']
                fail(module, result, 'CMCI request failed with response "{0}" reason "{1}"'
                     .format(cpsm_response_alt, cpsm_reason))

            if method != 'GET':
                result['changed'] = True
        except KeyError as e:
            # CMCI response parse error
            fail(module, result, 'Could not parse CMCI response: missing node "{0}"'.format(e.args[0]))

    except xmltodict.expat.ExpatError as e:
        # Content couldn't be parsed as XML
        # TODO: verbose log content if it couldn't be parsed?.  And maybe the other info from the ExpatError
        fail_e(module, result, 'CMCI response XML document could not be successfully parsed: {0}'.format(e), e)


def _get_url(params, option):
    cmci_host = params.get('cmci_host')
    cmci_port = params.get('cmci_port')
    resource = params.get('resource')
    t = resource.get('type')
    context = params.get('context')
    scope = params.get('scope')
    security_type = params.get('security_type', 'none')
    record_count = params.get('record_count')
    criteria = params.get('criteria')
    parameter = params.get('parameter')

    if security_type == 'none':
        scheme = 'http://'
    else:
        scheme = 'https://'
    url = scheme + cmci_host + ':' + cmci_port + '/CICSSystemManagement/' + t + '/' + context + '/'
    if scope:
        url = url + scope
    if option != 'define':
        # get, delete, put will all need CRITERIA
        if option == 'query':
            if record_count:
                url = url + '//' + str(record_count)

    request_params = None
    if criteria:
        if not request_params:
            request_params = {}
        request_params['CRITERIA'] = criteria

    if parameter:
        if not request_params:
            request_params = {}
        request_params['PARAMETER'] = parameter

    return url, t, request_params


def _create_session(module, result, security_type='none', crt=None, key=None, cmci_user=None, cmci_password=None, **kwargs):
    session = requests.Session()
    if security_type == 'certificate':
        if (crt is not None and crt.strip() != '') and (key is not None and key.strip() != ''):
            session.cert = (crt.strip(), key.strip())
        else:
            fail(module, result, 'HTTP setup error: cmci_cert/cmci_key are required ')
    # TODO: there's no clear distinction between unauthenticated HTTPS and authenticated HTTP
    if security_type == 'basic':
        if (cmci_user is not None and cmci_user.strip() != '') and (cmci_password is not None and cmci_password.strip() != ''):
            session.auth = (cmci_user.strip(), cmci_password.strip())
        else:
            fail(module, result, 'HTTP setup error: cmci_user/cmci_password are required')
    return session


def _do_request(module, result, session: requests.Session, method, url, params, data=None):
    try:
        response = session.request(method, url, verify=False, timeout=30, data=data, params=params)
        reason = response.reason if response.reason else response.status_code

        result['response'] = {'status_code': response.status_code, 'reason': reason}

        # TODO: in non-OK responses CPSM returns a body with error information
        # Can recreate this by supplying a malformed body with a create request.
        # We should surface this error information somehow.  Not sure what content type we get.
        if response.status_code != 200:
            fail(module, result, 'CMCI request returned non-OK status: {0}'.format(reason))

        return response
    except requests.exceptions.RequestException as e:
        cause = e
        if isinstance(cause, requests.exceptions.ConnectionError):
            cause = cause.args[0]
        if isinstance(cause, requests.packages.urllib3.exceptions.MaxRetryError):
            cause = cause.reason
        fail_e(module, result, 'Error performing CMCI request: {0}'.format(cause), e)


def fail(module, result, msg):
    module.fail_json(msg=msg, **result)


def fail_e(module, result, msg, exception):
    module.fail_json(msg=msg, exception=exception, **result)