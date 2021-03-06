# Original work Copyright 2017 Palantir Technologies, Inc. (MIT)
# See ThirdPartyNotices.txt in the project root for license information.
# All modifications Copyright (c) Robocorp Technologies Inc.
# All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License")
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http: // www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import argparse
import sys
import os


__file__ = os.path.abspath(__file__)
if __file__.endswith((".pyc", ".pyo")):
    __file__ = __file__[:-1]

LOG_FORMAT = "%(asctime)s UTC pid: %(process)d - %(threadName)s - %(levelname)s - %(name)s\n%(message)s\n\n"

_critical_error_log_file = os.path.join(
    os.path.expanduser("~"), "robotframework_ls_critical.log"
)


def _critical_msg(msg):
    with open(_critical_error_log_file, "a+") as stream:
        stream.write(msg + "\n")


def add_arguments(parser):
    from robotframework_ls.options import Options

    parser.description = "Python Language Server"

    parser.add_argument(
        "--tcp", action="store_true", help="Use TCP server instead of stdio"
    )
    parser.add_argument("--host", default=Options.host, help="Bind to this address")
    parser.add_argument(
        "--port", type=int, default=Options.port, help="Bind to this port"
    )

    parser.add_argument(
        "--log-file",
        help="Redirect logs to the given file instead of writing to stderr."
        "Has no effect if used with --log-config.",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=Options.verbose,
        help="Increase verbosity of log output, overrides log config file",
    )


def main(args=None, after_bind=lambda server: None, language_server_class=None):
    original_args = args if args is not None else sys.argv[1:]

    try:
        import robotframework_ls
    except ImportError:
        # Automatically add it to the path if __main__ is being executed.
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        import robotframework_ls  # @UnusedImport
    robotframework_ls.import_robocode_ls_core()

    from robotframework_ls.options import Setup, Options
    from robocode_ls_core.robotframework_log import (
        configure_logger,
        log_args_and_python,
        get_logger,
    )

    from robocode_ls_core.python_ls import (
        start_io_lang_server,
        start_tcp_lang_server,
        binary_stdio,
    )

    if language_server_class is None:
        from robotframework_ls.robotframework_ls_impl import (
            RobotFrameworkLanguageServer,
        )

        language_server_class = RobotFrameworkLanguageServer

    parser = argparse.ArgumentParser()
    add_arguments(parser)

    args = parser.parse_args(args=original_args)
    Setup.options = Options(args)
    verbose = args.verbose
    log_file = args.log_file or ""

    configure_logger("lsp", verbose, log_file)
    log = get_logger("robotframework_ls.__main__")
    log_args_and_python(log, original_args, robotframework_ls.__version__)

    if args.tcp:
        start_tcp_lang_server(
            args.host, args.port, language_server_class, after_bind=after_bind
        )
    else:
        stdin, stdout = binary_stdio()
        start_io_lang_server(stdin, stdout, language_server_class)


if __name__ == "__main__":
    try:
        main()
    except:
        # Critical error (the logging may not be set up properly).
        import traceback

        # Print to file and stderr.
        with open(_critical_error_log_file, "a+") as stream:
            traceback.print_exc(file=stream)

        traceback.print_exc()
