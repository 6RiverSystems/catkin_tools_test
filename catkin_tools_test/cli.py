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

from catkin_tools.argument_parsing import add_context_args
from catkin_tools.context import Context
from catkin_tools.execution import job_server
from catkin_tools.terminal_color import fmt

from .test import test_workspace
from .util import print_test_env


def main(opts):
    ctx = Context.load(opts.workspace, opts.profile, opts, append=True)

    if opts.get_env:
        return print_test_env(ctx, opts.get_env)

    job_server.initialize(
        max_jobs=4,
        max_load=None,
        gnu_make_enabled=False)

    return test_workspace(
        ctx,
        packages=opts.packages,
        tests=opts.tests,
        list_tests=opts.list_tests,
        n_jobs=int(opts.parallel_jobs or 6),
        force_color=opts.force_color,
        quiet=not opts.verbose,
        interleave_output=opts.interleave_output,
        no_status=opts.no_status,
        limit_status_rate=opts.limit_status_rate,
        no_notify=opts.no_notify)


def prepare_arguments(parser):
    add_context_args(parser)

    # What packages to test
    pkg_group = parser.add_argument_group('Packages', 'Control which packages have tests built and run.')
    add = pkg_group.add_argument
    add('packages', metavar='PKGNAME', nargs='*',
        help='Workspace packages to test. If no packages are given, then all the packages are tested.')
    add('--this', dest='test_this', action='store_true', default=False,
        help='Build the package containing the current working directory.')
    add('-j', '--jobs', default=None,
        help='Maximum number of build jobs to be distributed across active packages. (default is cpu count)')
    add('-p', '--parallel-packages', metavar='PACKAGE_JOBS', dest='parallel_jobs', default=None,
        help='Maximum number of packages allowed to be built in parallel (default is cpu count)')

    behavior_group = parser.add_mutually_exclusive_group() #'Testing', 'Selection of specific tests to run.')
    add = behavior_group.add_argument
    add('--list', dest='list_tests', action='store_true', default=False,
        help='Do not build or run, only list available tests in selected packages.')
    add('--tests', '-t', nargs='+', type=str, default=None,
        help='Specify exact tests to run.')
    add('--get-env', metavar='PKGNAME', type=str, default=None,
        help='Get environment to run tests for specific package.')

    behavior_group = parser.add_argument_group('Interface', 'The behavior of the command-line interface.')
    add = behavior_group.add_argument
    add('--verbose', '-v', action='store_true', default=False,
        help='Print output from commands in ordered blocks once the command finishes.')
    add('--interleave-output', '-i', action='store_true', default=False,
        help='Prevents ordering of command output when multiple commands are running at the same time.')
    add('--no-status', action='store_true', default=False,
        help='Suppresses status line, useful in situations where carriage return is not properly supported.')

    def status_rate_type(rate):
        rate = float(rate)
        if rate < 0:
            raise argparse.ArgumentTypeError("must be greater than or equal to zero.")
        return rate

    add('--limit-status-rate', '--status-rate', type=status_rate_type, default=10.0,
        help='Limit the update rate of the status bar to this frequency. Zero means unlimited. '
             'Must be positive, default is 10 Hz.')
    add('--no-notify', action='store_true', default=False,
        help='Suppresses system pop-up notification.')

    return parser
