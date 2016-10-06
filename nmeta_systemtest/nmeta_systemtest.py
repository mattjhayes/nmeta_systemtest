#!/usr/bin/python

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Run full suite of nmeta system regression tests
in an easy automated manner to make regression testing
nmeta updates a breeze...

Designed to fail as soon as there is an issue to avoid
unnecessary time waiting to be advised of regression issue that
needs fixing

Provides quantitative (performance) and qualitative (pass test) data

Requires Ansible and test network environment. See documentation for
details.
"""

import datetime
import os
import time
from os.path import expanduser
import sys

#*** Logging imports:
import logging
import logging.handlers
import coloredlogs

#*** Filename for results to be written to:
RESULTS_DIR = 'nmeta_systemtest_results'
LOGGING_FILENAME = 'test_results.txt'
LOGGING_FILE_LEVEL = logging.INFO
LOGGING_FILE_FORMAT = "%(asctime)s %(levelname)s: " \
                            "%(funcName)s: %(message)s"

#*** Parameters for capture of environment configuration:
ENVIRONMENT_PLAYBOOK = 'nmeta-full-regression-environment-template.yml'

#*** Parameters for regression of Static classification:
STATIC_REPEATS = 1
STATIC_TESTS = ["constrained-bw-tcp1234", "constrained-bw-tcp5555"]
STATIC_POLICY_1 = 'main_policy_regression_static.yaml'
STATIC_POLICY_2 = 'main_policy_regression_static_2.yaml'
STATIC_DURATION = 10
STATIC_PLAYBOOK = 'nmeta-full-regression-static-template.yml'
STATIC_PAUSE_SWITCH2CONTROLLER = 30
STATIC_SLEEP = 30
STATIC_TEST_FILES = ["pc1.example.com-1234-iperf_result.txt",
                    "pc1.example.com-5555-iperf_result.txt"]
STATIC_THRESHOLD_CONSTRAINED = 200000
STATIC_THRESHOLD_UNCONSTRAINED = 1000000

#*** Parameters for regression of Identity classification:
IDENTITY_REPEATS = 1
IDENTITY_TESTS = ["lg1-constrained-bw", "pc1-constrained-bw"]
IDENTITY_POLICY_1 = 'main_policy_regression_identity.yaml'
IDENTITY_POLICY_2 = 'main_policy_regression_identity_2.yaml'
IDENTITY_DURATION = 10
IDENTITY_PLAYBOOK = 'nmeta-full-regression-identity-template.yml'
IDENTITY_TCP_PORT = 5555
IDENTITY_PAUSE1_SWITCH2CONTROLLER = 10
IDENTITY_PAUSE2_LLDPLEARN = 30
IDENTITY_PAUSE3_INTERTEST = 6
IDENTITY_SLEEP = 30
IDENTITY_TEST_FILES = ["lg1.example.com-iperf_result.txt",
                    "pc1.example.com-iperf_result.txt"]
IDENTITY_THRESHOLD_CONSTRAINED = 200000
IDENTITY_THRESHOLD_UNCONSTRAINED = 1000000

#*** Parameters for regression of Statistical classification:
STATISTICAL_REPEATS = 1
STATISTICAL_TESTS = ['constrained-bw-iperf', 'unconstrained-bw-iperf']
STATISTICAL_POLICY_1 = 'main_policy_regression_statistical.yaml'
STATISTICAL_POLICY_2 = 'main_policy_regression_statistical_control.yaml'
STATISTICAL_DURATION = 10
STATISTICAL_PLAYBOOK = 'nmeta-full-regression-statistical-template.yml'
STATISTICAL_TCP_PORT = 5555
STATISTICAL_PAUSE_SWITCH2CONTROLLER = 10
STATISTICAL_SLEEP = 30
STATISTICAL_TEST_FILES = ["pc1.example.com-iperf_result.txt",]
STATISTICAL_THRESHOLD_CONSTRAINED = 280000
STATISTICAL_THRESHOLD_UNCONSTRAINED = 1000000

#*** Parameters for performance testing:
#*** Test effect of different classification policies on performance:
PERFORMANCE_TESTS = ['static', 'identity', 'statistical']
PERFORMANCE_COUNT = 30
PERFORMANCE_PLAYBOOK = 'nmeta-full-regression-performance-template.yml'
PERFORMANCE_PAUSE_SWITCH2CONTROLLER = 10
PERFORMANCE_SLEEP = 30

#*** Parameters for analysis of nmeta syslog events:
LOGROTATE_PLAYBOOK = 'nmeta-full-regression-logrotate-template.yml'
LOGCHECK_PLAYBOOK = 'nmeta-full-regression-logcheck-template.yml'
LOG_ERROR_FILENAME = 'errors_logged.txt'

#*** Ansible Playbook directory:
HOME_DIR = expanduser("~")
PLAYBOOK_DIR = os.path.join(HOME_DIR, 'automated_tests')

def main():
    """
    Main function of nmeta regression tests.
    Sets up logging, creates the timestamped directory
    and runs functions for the various regression test types
    """

    #*** Set up logging:
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    coloredlogs.install(level="DEBUG",
                logger=logger,
                fmt="%(asctime)s.%(msecs)03d %(name)s[%(process)d] " \
           "%(funcName)s %(levelname)s %(message)s", datefmt='%H:%M:%S')
    logger.info("Running full regression test of nmeta")

    #*** Timestamp for results root directory:
    timenow = datetime.datetime.now()
    timestamp = timenow.strftime("%Y%m%d%H%M%S")
    logger.info("root results timestamp is %s", timestamp)

    #*** Directory base path to write results to:
    results_dir = os.path.join(HOME_DIR, RESULTS_DIR)

    #*** Create root directory for results:
    os.chdir(results_dir)
    logger.debug("creating subdirectory %s", timestamp)
    os.mkdir(timestamp)
    basedir = os.path.join(results_dir, timestamp)
    logger.info("base directory is %s", basedir)

    #*** Set up logging to file in the root dir for these results:
    logging_file = os.path.join(basedir, LOGGING_FILENAME)
    logging_fh = logging.FileHandler(logging_file)
    logging_fh.setLevel(LOGGING_FILE_LEVEL)
    formatter = logging.Formatter(LOGGING_FILE_FORMAT)
    logging_fh.setFormatter(formatter)
    logger.addHandler(logging_fh)

    #*** TEMP:
    regression_performance(logger, basedir)

    #*** Capture environment settings:
    regression_environment(logger, basedir)

    #*** Run static regression testing:
    regression_static(logger, basedir)

    #*** Run identity regression testing:
    regression_identity(logger, basedir)

    #*** Run statistical regression testing:
    regression_statistical(logger, basedir)

    #*** Run performance baseline tests:
    regression_performance(logger, basedir)

    #*** And we're done!:
    logger.info("All testing finished, that's a PASS!")
    logger.info("See test report at %s/%s", basedir, LOGGING_FILENAME)

def regression_environment(logger, basedir):
    """
    Capture details of the environment including info
    on the nmeta build
    """
    extra_vars = {'results_dir': basedir + "/"}
    playbook_cmd = build_playbook(ENVIRONMENT_PLAYBOOK, extra_vars,
                                                                logger)
    os.system(playbook_cmd)

def regression_static(logger, basedir):
    """
    Nmeta static classification regression testing
    """
    logger.info("running static regression testing")
    subdir = 'static'
    #*** Create subdirectory to write results to:
    os.chdir(basedir)
    os.mkdir(subdir)
    test_basedir = os.path.join(basedir, subdir)
    #*** Run tests
    for i in range(STATIC_REPEATS):
        logger.debug("iteration %s of %s", i+1, STATIC_REPEATS)
        for test in STATIC_TESTS:
            #*** Timestamp for specific test subdirectory:
            timenow = datetime.datetime.now()
            testdir_timestamp = timenow.strftime("%Y%m%d%H%M%S")
            logger.info("running test=%s", test)
            test_dir = os.path.join(test_basedir, test,
                                                    testdir_timestamp)
            rotate_log(logger)
            if test == 'constrained-bw-tcp1234':
                policy_name = STATIC_POLICY_1
            elif test == 'constrained-bw-tcp5555':
                policy_name = STATIC_POLICY_2
            else:
                logger.critical("ERROR: unknown static test %s", test)
                sys.exit()
            extra_vars = {'duration': str(STATIC_DURATION),
                        'results_dir': test_dir + "/",
                        'policy_name': policy_name,
                        'pause1': str(STATIC_PAUSE_SWITCH2CONTROLLER)}
            playbook_cmd = build_playbook(STATIC_PLAYBOOK,
                                            extra_vars, logger)
            logger.info("running Ansible playbook...")
            os.system(playbook_cmd)

            #*** Analyse static regression results:
            logger.debug("Reading results in directory %s", test_dir)
            results = {}
            for filename in STATIC_TEST_FILES:
                results[filename] = get_iperf_bw(test_dir, filename)

            #*** Validate that the results are as expected:
            if test == STATIC_TESTS[0]:
                constrained = results[STATIC_TEST_FILES[0]]
                unconstrained = results[STATIC_TEST_FILES[1]]
            elif test == STATIC_TESTS[1]:
                constrained = results[STATIC_TEST_FILES[1]]
                unconstrained = results[STATIC_TEST_FILES[0]]
            else:
                #*** Unknown error condition:
                logger.critical("UNKNOWN TEST TYPE. test=%s", test)
                sys.exit("Please fix this test code. Exiting...")
            logger.info("validating bw constrained=%s unconstrained=%s",
                                             constrained, unconstrained)
            assert constrained < STATIC_THRESHOLD_CONSTRAINED
            assert unconstrained > STATIC_THRESHOLD_UNCONSTRAINED
            logger.info("STATIC TC TEST PASSED. test=%s", test)
            logger.info("bandwidth constrained=%s unconstrained=%s",
                                constrained, unconstrained)

            #*** Check for any logs that are CRITICAL or ERROR:
            check_log(logger, test_dir)

            logger.info("Sleeping... zzzz")
            time.sleep(STATIC_SLEEP)

def regression_identity(logger, basedir):
    """
    Nmeta identity classification regression testing
    """
    logger.info("running identity regression testing")
    subdir = 'identity'
    #*** Create subdirectory to write results to:
    os.chdir(basedir)
    os.mkdir(subdir)
    test_basedir = os.path.join(basedir, subdir)
    #*** Run tests
    for i in range(IDENTITY_REPEATS):
        logger.debug("iteration %s of %s", i+1, IDENTITY_REPEATS)
        for test in IDENTITY_TESTS:
            #*** Timestamp for specific test subdirectory:
            timenow = datetime.datetime.now()
            testdir_timestamp = timenow.strftime("%Y%m%d%H%M%S")
            logger.info("running test=%s", test)
            test_dir = os.path.join(test_basedir, test,
                                                    testdir_timestamp)
            rotate_log(logger)
            if test == "lg1-constrained-bw":
                policy_name = IDENTITY_POLICY_1
            elif test == "pc1-constrained-bw":
                policy_name = IDENTITY_POLICY_2
            else:
                logger.critical("ERROR: unknown identity test %s", test)
                sys.exit()
            extra_vars = {'duration': str(IDENTITY_DURATION),
                        'results_dir': test_dir + "/",
                        'policy_name': policy_name,
                        'tcp_port': str(IDENTITY_TCP_PORT),
                        'pause1':
                                str(IDENTITY_PAUSE1_SWITCH2CONTROLLER),
                        'pause2': str(IDENTITY_PAUSE2_LLDPLEARN),
                        'pause3': str(IDENTITY_PAUSE3_INTERTEST)}
            playbook_cmd = build_playbook(IDENTITY_PLAYBOOK,
                                            extra_vars, logger)
            logger.info("running Ansible playbook...")
            os.system(playbook_cmd)

            #*** Analyse identity regression results:
            logger.debug("Reading results in directory %s", test_dir)
            results = {}
            for filename in IDENTITY_TEST_FILES:
                results[filename] = get_iperf_bw(test_dir, filename)

            #*** Validate that the results are as expected:
            if test == IDENTITY_TESTS[0]:
                constrained = results[IDENTITY_TEST_FILES[0]]
                unconstrained = results[IDENTITY_TEST_FILES[1]]
            elif test == IDENTITY_TESTS[1]:
                constrained = results[IDENTITY_TEST_FILES[1]]
                unconstrained = results[IDENTITY_TEST_FILES[0]]
            else:
                #*** Unknown error condition:
                logger.critical("UNKNOWN TEST TYPE. test=%s", test)
                sys.exit("Please fix this test code. Exiting...")
            logger.info("validating bw constrained=%s unconstrained=%s",
                                             constrained, unconstrained)
            assert constrained < IDENTITY_THRESHOLD_CONSTRAINED
            assert unconstrained > IDENTITY_THRESHOLD_UNCONSTRAINED
            logger.info("IDENTITY TC TEST PASSED. test=%s", test)
            logger.info("bandwidth constrained=%s unconstrained=%s",
                                constrained, unconstrained)

            #*** Check for any logs that are CRITICAL or ERROR:
            check_log(logger, test_dir)

            logger.info("Sleeping... zzzz")
            time.sleep(IDENTITY_SLEEP)

def regression_statistical(logger, basedir):
    """
    Nmeta statistical classification regression testing
    """
    logger.info("running statistical regression testing")
    subdir = 'statistical'
    #*** Create subdirectory to write results to:
    os.chdir(basedir)
    os.mkdir(subdir)
    test_basedir = os.path.join(basedir, subdir)
    #*** Run tests
    for i in range(STATISTICAL_REPEATS):
        logger.debug("iteration %s of %s", i+1, STATISTICAL_REPEATS)
        for test in STATISTICAL_TESTS:
            #*** Timestamp for specific test subdirectory:
            timenow = datetime.datetime.now()
            testdir_timestamp = timenow.strftime("%Y%m%d%H%M%S")
            logger.info("running test=%s", test)
            test_dir = os.path.join(test_basedir, test,
                                                    testdir_timestamp)
            rotate_log(logger)
            if test == 'constrained-bw-iperf':
                policy_name = STATISTICAL_POLICY_1
            elif test == 'unconstrained-bw-iperf':
                policy_name = STATISTICAL_POLICY_2
            else:
                logger.critical("ERROR: unknown statistical test %s",
                                                                   test)
                sys.exit()
            extra_vars = {'duration': str(STATISTICAL_DURATION),
                        'results_dir': test_dir + "/",
                        'policy_name': policy_name,
                        'tcp_port': str(STATISTICAL_TCP_PORT),
                        'pause1':
                               str(STATISTICAL_PAUSE_SWITCH2CONTROLLER)}
            playbook_cmd = build_playbook(STATISTICAL_PLAYBOOK,
                                            extra_vars, logger)
            logger.info("running Ansible playbook...")
            os.system(playbook_cmd)

            #*** Analyse statistical regression results:
            logger.debug("Reading results in directory %s", test_dir)
            results = {}
            for filename in STATISTICAL_TEST_FILES:
                results[filename] = get_iperf_bw(test_dir, filename)

            #*** Validate that the results are as expected:
            if test == STATISTICAL_TESTS[0]:
                constrained = results[STATISTICAL_TEST_FILES[0]]
                logger.info("validating statistical bw constrained=%s",
                                                            constrained)
                assert constrained < STATISTICAL_THRESHOLD_CONSTRAINED
            elif test == STATISTICAL_TESTS[1]:
                unconstrained = results[STATISTICAL_TEST_FILES[0]]
                logger.info("validating statistical bw unconstrained=%s"
                                                        , unconstrained)
                assert unconstrained > \
                                     STATISTICAL_THRESHOLD_UNCONSTRAINED
            else:
                #*** Unknown error condition:
                logger.critical("UNKNOWN TEST TYPE. test=%s", test)
                sys.exit("Please fix this test code. Exiting...")

            logger.info("STATISTICAL TC TEST PASSED. test=%s", test)

            #*** Check for any logs that are CRITICAL or ERROR:
            check_log(logger, test_dir)

            logger.info("Sleeping... zzzz")
            time.sleep(STATISTICAL_SLEEP)

def regression_performance(logger, basedir):
    """
    Nmeta performance regression testing
    """
    logger.info("running performance regression testing")
    subdir = 'performance'
    #*** Create subdirectory to write results to:
    os.chdir(basedir)
    os.mkdir(subdir)
    test_basedir = os.path.join(basedir, subdir)
    #*** Run tests:
    for test in PERFORMANCE_TESTS:
        logger.info("running test=%s", test)
        test_dir = os.path.join(test_basedir, test)
        rotate_log(logger)
        if test == "static":
            policy_name = STATIC_POLICY_1
        elif test == "identity":
            policy_name = IDENTITY_POLICY_1
        elif test == "statistical":
            policy_name = STATISTICAL_POLICY_1
        else:
            logger.critical("ERROR: unknown performance test %s", test)
            sys.exit()
        extra_vars = {'count': str(PERFORMANCE_COUNT),
                        'results_dir': test_dir + "/",
                        'policy_name': policy_name,
                        'pause1':
                               str(PERFORMANCE_PAUSE_SWITCH2CONTROLLER)}
        playbook_cmd = build_playbook(PERFORMANCE_PLAYBOOK,
                                            extra_vars, logger)
        logger.info("running Ansible playbook...")
        os.system(playbook_cmd)

        #*** Analyse performance results:

        # TBD

        #*** Check for any logs that are CRITICAL or ERROR:
        check_log(logger, test_dir)

        logger.info("Sleeping... zzzz")
        time.sleep(PERFORMANCE_SLEEP)

#==================== helper functions ====================

def get_iperf_bw(test_dir, filename):
    """
    Passed the directory and filename of an Iperf result
    file and return the reported bandwidth or exit if error
    """
    filename_full = os.path.join(test_dir, filename)
    with open(filename_full) as filehandle:
        data = filehandle.read()
        data = data.split(",")
        #*** The result is position 8 and remove trailing newline:
        return int(str(data[8]).rstrip())

def build_playbook(playbook_name, extra_vars, logger):
    """
    Passed an Ansible Playbook name, and a dictionary of extra
    vars to pass to it, and return a properly formatted string that
    will run the Playbook from the command line
    """
    playbook = os.path.join(PLAYBOOK_DIR, playbook_name)
    logger.debug("playbook is %s", playbook)
    playbook_cmd = "ansible-playbook " + playbook
    if extra_vars:
        playbook_cmd += " --extra-vars \""
        for key, value in extra_vars.iteritems():
            playbook_cmd += key + "=" + value + " "
        playbook_cmd += "\""
    logger.debug("playbook_cmd=%s", playbook_cmd)
    return playbook_cmd

def rotate_log(logger):
    """
    Run an Ansible playbook to rotate the nmeta log
    so that it is fresh for analysis post test
    """
    logger.info("Rotating nmeta syslog output for freshness")
    extra_vars = {}
    playbook_cmd = build_playbook(LOGROTATE_PLAYBOOK, extra_vars,
                                                                logger)
    logger.info("running Ansible playbook...")
    os.system(playbook_cmd)

def check_log(logger, test_dir):
    """
    Check the nmeta log file to see if it has any log events that
    should cause the test to fail so that code can be fixed
    """
    logger.info("Checking nmeta syslog for error or critical messages")
    extra_vars = {'results_dir': test_dir + "/",
                'error_filename': LOG_ERROR_FILENAME}
    playbook_cmd = build_playbook(LOGCHECK_PLAYBOOK, extra_vars,
                                                                logger)
    logger.info("running Ansible playbook...")
    os.system(playbook_cmd)
    #*** Presence of non-zero file indicates ERROR and/or CRITICAL logs:
    error_file = os.path.join(test_dir, LOG_ERROR_FILENAME)
    if os.path.isfile(error_file):
        if os.stat(error_file).st_size > 0:
            logger.critical("ERROR and/or CRITICAL logs need attention")
            logger.info("Check file %s", error_file)
            sys.exit()

if __name__ == "__main__":
    #*** Run the main function
    main()
