# Copyright 2016 Clearpath Robotics Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from __future__ import print_function

from catkin_pkg.packages import find_packages
from catkin_tools.common import format_env_dict
from catkin_tools.resultspace import get_resultspace_environment

import os
import sys


_which_cache = {}

def which(program):
    global _which_cache
    if program not in _which_cache:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            executable = os.path.join(path, program)
            if os.path.exists(executable):
                _which_cache[program] = executable
                break

    return _which_cache[program]


def loadenv(logger, event_queue, job_env, package, context):
    if context.install:
        raise ValueError('Cannot test with installed workspace.')
    env_loader_path = context.package_final_path(package)

    job_env.update(get_resultspace_environment(
        env_loader_path,
        base_env=job_env,
        quiet=True,
        cached=context.use_env_cache,
        strict=False))
    return 0


def print_test_env(context, package_name):
    workspace_packages = find_packages(context.source_space_abs, exclude_subspaces=True, warnings=[])
    # Load the environment used by this package for testing.
    for pth, pkg in workspace_packages.items():
        if pkg.name == package_name:
            environ = dict(os.environ)
            loadenv(None, None, environ, pkg, context)
            print(format_env_dict(environ))
            return 0
    print('[test] Error: Package `{}` not in workspace.'.format(package_name), file=sys.stderr)
    return 1


