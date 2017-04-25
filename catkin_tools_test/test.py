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

import os
import re
import time
import traceback
import yaml

try:
    # Python3
    from queue import Queue
except ImportError:
    # Python2
    from Queue import Queue

from catkin_pkg.packages import find_packages
from catkin_pkg.package import parse_package

from catkin_tools.common import log
from catkin_tools.common import wide_log

from catkin_tools.execution.controllers import ConsoleStatusController
from catkin_tools.execution.executor import execute_jobs
from catkin_tools.execution.executor import run_until_complete
from catkin_tools.execution.jobs import Job
from catkin_tools.execution.stages import CommandStage
from catkin_tools.execution.stages import FunctionStage
from catkin_tools.terminal_color import fmt

from catkin_tools.jobs.utils import makedirs

from .util import which


class UnconfiguredPackage(Exception):
    def __init__(self, package):
        self.package = package


def get_packages_to_test(context, packages):
    packages_to_test = find_packages(context.source_space_abs, exclude_subspaces=True, warnings=[]).values()

    if packages:
        # One or more package names specified explicitly by the user.
        packages_to_test = [package for package in packages_to_test if package.name in packages]
    else:
        # No packages specified, default to everything in workspace, subject to whitelist and blacklist.
        def filter_whitelist_blacklist(packages):
            for package in packages:
                if context.whitelist and package.name not in context.whitelist:
                    continue
                if context.blacklist and package.name in context.blacklist:
                    continue
                yield package
        packages_to_test = filter_whitelist_blacklist(packages_to_test)

    # Filter out metapackages and build_type values we don't support.
    def filter_exports(packages):
        for package in packages:
            keep = True
            for export in package.exports:
                if export.tagname == 'metapackage':
                    keep = False
                if export.tagname == 'build_type':
                    keep = False
            if keep:
                yield package
    packages_to_test = filter_exports(packages_to_test)

    return list(packages_to_test)


def get_packages_tests(context, packages_to_test):
    result = []
    for package in packages_to_test:
        package_build_space = os.path.join(context.build_space_abs, package.name)
        package_build_cmakefiles = os.path.join(package_build_space, 'CMakeFiles')
        if not os.path.exists(package_build_cmakefiles):
            raise UnconfiguredPackage(package)

        package_tests = []
        pattern = 'run_tests_%s_(.*?).dir' % package.name
        for target_dir in os.listdir(package_build_cmakefiles):
            m = re.match(pattern, target_dir)
            if m:
                package_tests.append(m.group(1))

        if package_tests:
            result.append((package, package_tests))
    return result


def create_package_job(context, package, package_tests):
    build_space = os.path.join(context.build_space_abs, package.name)
    if not os.path.exists(os.path.join(build_space, 'Makefile')):
        raise

    test_results_space = os.path.join(context.build_space_abs, '..', 'test_results', package.name)
    package_path_abs = os.path.join(context.source_space_abs, package_path)

    stages = []
    #stages.append()

    return Job(jid=package.name, deps=deps, env={}, stages=stages)


def test_workspace(
    context,
    packages=None,
    tests=None,
    list_tests=False,
    start_with=None,
    n_jobs=None,
    force_color=False,
    quiet=False,
    interleave_output=False,
    no_status=False,
    limit_status_rate=10.0,
    no_notify=False,
    summarize_build=None
):
    pre_start_time = time.time()

    # Get our list of packages based on what's in the source space and our
    # command line switches.
    packages_to_test = get_packages_to_test(context, packages)
    if len(packages_to_test) == 0:
        log(fmt('[test] No tests in the available packages.'))

    # Get the full list of tests available in those packages, as configured.
    packages_tests = get_packages_tests(context, packages_to_test)

    if list_tests:
        # Don't build or run, just list available targets.
        log(fmt('[test] Tests available in workspace packages:'))
        for package, tests in sorted(packages_tests):
            log(fmt('[test] * %s' % package.name))
            for test in sorted(tests):
                log(fmt('[test]   - %s' % test))
        return 0

    else:
        jobs = []

        # Construct jobs for running tests.
        for package in packages_tests:
            jobs.append(create_package_job(context, package, package_tests))

        # Queue for communicating status.
        event_queue = Queue()

        try:
            # Spin up status output thread.
            status_thread = ConsoleStatusController(
                'test',
                ['package', 'packages'],
                jobs,
                n_jobs,
                [pkg.name for _, pkg in context.packages],
                [p for p in context.whitelist],
                [p for p in context.blacklist],
                event_queue,
                show_notifications=not no_notify,
                show_active_status=not no_status,
                show_buffered_stdout=not quiet and not interleave_output,
                show_buffered_stderr=not interleave_output,
                show_live_stdout=interleave_output,
                show_live_stderr=interleave_output,
                show_stage_events=not quiet,
                show_full_summary=(summarize_build is True),
                pre_start_time=pre_start_time,
                active_status_rate=limit_status_rate)
            status_thread.start()

            # Block while running N jobs asynchronously
            try:
                all_succeeded = run_until_complete(execute_jobs(
                    'test',
                    jobs,
                    None,
                    event_queue,
                    context.log_space_abs,
                    max_toplevel_jobs=n_jobs))

            except Exception:
                status_thread.keep_running = False
                all_succeeded = False
                status_thread.join(1.0)
                wide_log(str(traceback.format_exc()))
            status_thread.join(1.0)

            return 0 if all_succeeded else 1

        except KeyboardInterrupt:
            wide_log("[test] Interrupted by user!")
            event_queue.put(None)

            return 130  # EOWNERDEAD
