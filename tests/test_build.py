import runpy
import unittest
from pathlib import Path
from unittest import mock

from setuptools import Distribution, Extension
from setuptools._distutils.ccompiler import new_compiler


class TestBuildExt(unittest.TestCase):
    def test_reinitialized_command_uses_fresh_compiler(self):
        setup_py = Path(__file__).parents[1] / "setup.py"
        with mock.patch("setuptools.setup") as setup:
            runpy.run_path(str(setup_py))

        build_ext = setup.call_args.kwargs["cmdclass"]["build_ext"]
        distribution = Distribution({
            "cmdclass": {"build_ext": build_ext},
            "ext_modules": [Extension("test", ["test.c"])],
        })
        command = distribution.get_command_obj("build_ext")
        command.ensure_finalized()
        command.compiler = new_compiler()

        distribution.reinitialize_command("build_ext")
        command.build_extensions = mock.Mock()
        command.run()

        command.build_extensions.assert_called_once_with()
