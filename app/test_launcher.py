"""Behavioral tests for the PowerShell simulation launcher.

The fake interpreter is a small .cmd program in an app-local temporary folder.
It records invocations and returns controlled import/server exit codes without
starting training or a server.
"""
from contextlib import contextmanager
import os
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile
import unittest


APP = Path(__file__).resolve().parent
ROOT = APP.parent
SCRIPT = APP / "start-simulation.ps1"
PWSH = shutil.which("pwsh")

FAKE_PYTHON = r"""@echo off
>>"%LAUNCHER_LOG%" echo ENV:%FAKE_DEP_FAIL%
>>"%LAUNCHER_LOG%" echo %*
if "%1"=="-c" goto probe
if "%1"=="-m" exit /b %FAKE_SERVER_EXIT%
exit /b 64
:probe
set /p PROBE_NUMBER=<"%FAKE_PROBE_COUNTER%"
if not defined PROBE_NUMBER set PROBE_NUMBER=0
set /a PROBE_NUMBER+=1 >nul
>"%FAKE_PROBE_COUNTER%" echo %PROBE_NUMBER%
if "%PROBE_NUMBER%"=="2" (
  if "%FAKE_OPTIONAL_CAP%"=="1" exit /b 0
  exit /b 1
)
if "%FAKE_DEP_FAIL%"=="1" exit /b 42
echo %FAKE_INTERPRETER%
exit /b 0
"""


@contextmanager
def fake_interpreter(*, dep_fail="0", optional_cap="0", server_exit="0"):
    """Create the controlled interpreter and its private invocation log."""
    with tempfile.TemporaryDirectory(prefix=".launcher-test-", dir=APP) as temp:
        folder = Path(temp)
        executable = folder / "fake-python.cmd"
        log = folder / "calls.log"
        counter = folder / "probe-count.txt"
        executable.write_text(FAKE_PYTHON, encoding="ascii", newline="\r\n")
        counter.write_text("0\n", encoding="ascii")
        env = os.environ.copy()
        env.update({
            "LAUNCHER_LOG": str(log),
            "FAKE_PROBE_COUNTER": str(counter),
            "FAKE_INTERPRETER": str(executable.resolve()),
            "FAKE_DEP_FAIL": dep_fail,
            "FAKE_OPTIONAL_CAP": optional_cap,
            "FAKE_SERVER_EXIT": server_exit,
            "PYTHONDONTWRITEBYTECODE": "1",
        })
        yield executable.resolve(), log, env


def free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def invoke_launcher(executable, port, env, *, cwd=ROOT, script=SCRIPT):
    if not PWSH:
        raise RuntimeError("pwsh is required for launcher behavior tests")
    return subprocess.run(
        [PWSH, "-NoLogo", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File",
         str(script.resolve()), "-Python", str(executable), "-Port", str(port), "-SkipVendor"],
        cwd=str(cwd), env=env, capture_output=True, text=True, timeout=20,
    )


def successful_launch(port=None, *, cwd=ROOT):
    """Run the launcher once and return its process result and fake calls."""
    port = free_port() if port is None else port
    with fake_interpreter(server_exit="0") as (executable, log, env):
        result = invoke_launcher(executable, port, env, cwd=cwd)
        calls = log.read_text(encoding="utf-8").splitlines() if log.exists() else []
        return result, calls, str(executable), port


@unittest.skipUnless(PWSH, "pwsh is required for launcher behavior tests")
class LauncherBehaviorTests(unittest.TestCase):
    def test_success_checks_dependencies_and_passes_server_arguments_and_exit(self):
        with fake_interpreter(server_exit="23") as (executable, log, env):
            port = free_port()
            result = invoke_launcher(executable, port, env)
            calls = log.read_text(encoding="utf-8").splitlines() if log.exists() else []
        self.assertEqual(result.returncode, 23, result.stdout + result.stderr)
        self.assertIn(str(executable), result.stdout, "the selected absolute interpreter is not printed")
        self.assertIn(f"localhost:{port}/agents", result.stdout)
        self.assertIn(f"localhost:{port}/results", result.stdout)
        self.assertTrue(any("fastapi" in call and "uvicorn" in call and "numpy" in call
                            and "gymnasium" in call for call in calls), calls)
        self.assertTrue(any(f"-m app.server --simulation --http-port {port}" in call for call in calls), calls)
        self.assertIn("stable-baselines3", result.stdout.lower(), "the optional capability note is missing")

    def test_absolute_script_path_works_from_an_unrelated_working_directory(self):
        with tempfile.TemporaryDirectory(prefix=".launcher-cwd-", dir=APP) as cwd:
            result, calls, executable, port = successful_launch(cwd=Path(cwd))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(executable, result.stdout)
        self.assertTrue(any(f"-m app.server --simulation --http-port {port}" in call for call in calls), calls)

    def test_invalid_interpreter_fails_before_server_start(self):
        with tempfile.TemporaryDirectory(prefix=".launcher-invalid-", dir=APP) as temp:
            missing = Path(temp) / "missing-python.exe"
            env = os.environ.copy()
            env["PYTHONDONTWRITEBYTECODE"] = "1"
            result = invoke_launcher(missing, free_port(), env)
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn("app.server", result.stdout + result.stderr)

    def test_missing_required_import_fails_without_starting_server(self):
        with fake_interpreter(dep_fail="1") as (executable, log, env):
            result = invoke_launcher(executable, free_port(), env)
            calls = log.read_text(encoding="utf-8").splitlines() if log.exists() else []
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(calls and all("app.server" not in call for call in calls), calls)

    def test_occupied_local_port_fails_before_interpreter_start(self):
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind(("127.0.0.1", 0))
        listener.listen(1)
        port = listener.getsockname()[1]
        try:
            with fake_interpreter() as (executable, log, env):
                result = invoke_launcher(executable, port, env)
                calls = log.read_text(encoding="utf-8").splitlines() if log.exists() else []
        finally:
            listener.close()
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(calls, [], "an occupied port should be detected before interpreter probes")

    def test_missing_vendor_resource_fails_without_starting_python_when_skip_is_requested(self):
        with tempfile.TemporaryDirectory(prefix=".launcher-vendor-", dir=APP) as temp:
            fixture_root = Path(temp)
            fixture_app = fixture_root / "app"
            fixture_app.mkdir()
            fixture_script = fixture_app / "start-simulation.ps1"
            fixture_script.write_text(SCRIPT.read_text(encoding="utf-8"), encoding="utf-8")
            with fake_interpreter() as (executable, log, env):
                result = invoke_launcher(executable, free_port(), env, cwd=fixture_root, script=fixture_script)
                calls = log.read_text(encoding="utf-8").splitlines() if log.exists() else []
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Three.js is not vendored", result.stdout + result.stderr)
        self.assertEqual(calls, [], "vendor failure should stop before interpreter validation")


@unittest.skipUnless(os.name == "nt" and PWSH, "Windows and PowerShell are required")
class CmdLauncherBehaviorTests(unittest.TestCase):
    def invoke(self, executable, port, env):
        # Exercise the actual batch entry point, including spaces in both paths.
        command = f'"{APP / "start.cmd"}" -Python "{executable}" -Port {port} -SkipVendor'
        return subprocess.run(
            f'"{os.environ.get("COMSPEC", "cmd.exe")}" /d /s /c "{command}"',
            cwd=str(APP / "static"), env=env, input="\n", capture_output=True,
            text=True, timeout=20,
        )

    def test_cmd_from_another_directory_forwards_options_and_server_exit(self):
        with fake_interpreter(server_exit="23") as (executable, log, env):
            port = free_port()
            result = self.invoke(executable, port, env)
            calls = log.read_text(encoding="utf-8").splitlines() if log.exists() else []
        self.assertEqual(result.returncode, 23, result.stdout + result.stderr)
        self.assertIn(str(executable), result.stdout)
        self.assertTrue(any(f"-m app.server --simulation --http-port {port}" in call for call in calls), calls)

    def test_cmd_dependency_failure_never_starts_the_server(self):
        with fake_interpreter(dep_fail="1") as (executable, log, env):
            result = self.invoke(executable, free_port(), env)
            calls = log.read_text(encoding="utf-8").splitlines() if log.exists() else []
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(calls, "the batch entry point did not reach the interpreter probe")
        self.assertTrue(all("app.server" not in call for call in calls), calls)


def assert_launcher_page_contract(test_case, page):
    """Shared, executed launch contract used by the agent/results suites."""
    result, calls, executable, port = successful_launch()
    test_case.assertEqual(result.returncode, 0, result.stdout + result.stderr)
    test_case.assertIn(executable, result.stdout)
    test_case.assertIn(f"localhost:{port}/{page}", result.stdout)
    test_case.assertLess(result.stdout.index(f"localhost:{port}/agents"),
                         result.stdout.index(f"localhost:{port}/results"))
    test_case.assertIn("stable-baselines3", result.stdout.lower())
    test_case.assertTrue(any("fastapi" in call and "uvicorn" in call
                             and "numpy" in call and "gymnasium" in call for call in calls), calls)
    test_case.assertTrue(any(f"-m app.server --simulation --http-port {port}" in call for call in calls), calls)


if __name__ == "__main__":
    unittest.main()
