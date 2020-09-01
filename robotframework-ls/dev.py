"""
This is a script to help with the automation of common development tasks.

It requires 'fire' to be installed for the command line automation (i.e.: pip install fire).

Some example commands:

    python -m dev set-version 0.0.2
    python -m dev check-tag-version
    python -m dev vendor-robocorp-ls-core
"""
import sys
import os

__file__ = os.path.abspath(__file__)

if not os.path.exists(os.path.join(os.path.abspath("."), "dev.py")):
    raise RuntimeError('Please execute commands from the directory containing "dev.py"')

import fire

try:
    import robotframework_ls
except ImportError:
    # I.e.: add relative path (the cwd must be the directory containing this file).
    sys.path.append("src")
    import robotframework_ls

robotframework_ls.import_robocode_ls_core()


def _fix_contents_version(contents, version):
    import re

    contents = re.sub(
        r"(version\s*=\s*)\"\d+\.\d+\.\d+", r'\1"%s' % (version,), contents
    )
    contents = re.sub(
        r"(__version__\s*=\s*)\"\d+\.\d+\.\d+", r'\1"%s' % (version,), contents
    )
    contents = re.sub(
        r"(\"version\"\s*:\s*)\"\d+\.\d+\.\d+", r'\1"%s' % (version,), contents
    )
    contents = re.sub(
        r"(blob/robotframework-lsp)-\d+\.\d+\.\d+", r"\1-%s" % (version,), contents
    )

    return contents


class Dev(object):
    def set_version(self, version):
        """
        Sets a new version for robotframework-lsp in all the needed files.
        """

        def update_version(version, filepath):
            with open(filepath, "r") as stream:
                contents = stream.read()

            new_contents = _fix_contents_version(contents, version)
            if contents != new_contents:
                with open(filepath, "w") as stream:
                    stream.write(new_contents)

        update_version(version, os.path.join(".", "package.json"))
        update_version(version, os.path.join(".", "src", "setup.py"))
        update_version(
            version, os.path.join(".", "src", "robotframework_ls", "__init__.py")
        )

    def get_tag(self):
        import subprocess

        # i.e.: Gets the last tagged version
        cmd = "git describe --tags --abbrev=0 --match robotframework*".split()
        popen = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        stdout, stderr = popen.communicate()

        # Something as: b'robotframework-lsp-0.0.1'
        if sys.version_info[0] >= 3:
            stdout = stdout.decode("utf-8")
        stdout = stdout.strip()
        return stdout

    def check_tag_version(self):
        """
        Checks if the current tag matches the latest version (exits with 1 if it
        does not match and with 0 if it does match).
        """
        tag = self.get_tag()
        version = tag[tag.rfind("-") + 1 :]

        if robotframework_ls.__version__ == version:
            sys.stderr.write("Version matches (%s) (exit(0))\n" % (version,))
            sys.exit(0)
        else:
            sys.stderr.write(
                "Version does not match (lsp: %s != tag: %s) (exit(1))\n"
                % (robotframework_ls.__version__, version)
            )
            sys.exit(1)

    def vendor_robocode_ls_core(self):
        """
        Vendors robocorp_ls_core into robotframework_ls/vendored.
        """
        import shutil

        src_core = os.path.join(
            os.path.dirname(__file__),
            "..",
            "robocorp-python-ls-core",
            "src",
            "robocorp_ls_core",
        )
        vendored_dir = os.path.join(
            os.path.dirname(__file__),
            "src",
            "robotframework_ls",
            "vendored",
            "robocorp_ls_core",
        )
        print("Copying from: %s to %s" % (src_core, vendored_dir))
        try:
            shutil.rmtree(vendored_dir)
        except:
            pass
        import time

        time.sleep(0.2)
        shutil.copytree(src_core, vendored_dir)
        print("Finished vendoring.")

    def fix_readme(self):
        """
        Updates the links in the README.md to match the current tagged version.
        To be called during release.
        """
        import re

        readme = os.path.join(os.path.dirname(__file__), "README.md")
        with open(readme, "r") as f:
            content = f.read()
        new_content = re.sub(
            r"\(docs/",
            r"(https://github.com/robocorp/robotframework-lsp/tree/%s/robotframework-ls/docs/"
            % (self.get_tag(),),
            content,
        )
        with open(readme, "w") as f:
            f.write(new_content)


def test_lines():
    """
    Check that the replace matches what we expect.
    
    Things we must match:

        version="0.0.1"
        "version": "0.0.1",
        __version__ = "0.0.1"
        https://github.com/robocorp/robotframework-lsp/blob/robotframework-lsp-0.1.1/robotframework-ls/README.md
    """
    from robocorp_ls_core.unittest_tools.compare import compare_lines

    contents = _fix_contents_version(
        """
        version="0.0.198"
        version = "0.0.1"
        "version": "0.0.1",
        "version":"0.0.1",
        "version" :"0.0.1",
        __version__ = "0.0.1"
        https://github.com/robocorp/robotframework-lsp/blob/robotframework-lsp-0.1.1/robotframework-ls/README.md
        """,
        "3.7.1",
    )

    expected = """
        version="3.7.1"
        version = "3.7.1"
        "version": "3.7.1",
        "version":"3.7.1",
        "version" :"3.7.1",
        __version__ = "3.7.1"
        https://github.com/robocorp/robotframework-lsp/blob/robotframework-lsp-3.7.1/robotframework-ls/README.md
        """

    compare_lines(contents.splitlines(), expected.splitlines())


if __name__ == "__main__":
    TEST = False
    if TEST:
        test_lines()
    else:
        # Workaround so that fire always prints the output.
        # See: https://github.com/google/python-fire/issues/188
        def Display(lines, out):
            text = "\n".join(lines) + "\n"
            out.write(text)

        from fire import core

        core.Display = Display

        fire.Fire(Dev())
