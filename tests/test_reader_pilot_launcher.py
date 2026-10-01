"""Local launcher safety tests: all processes, ports and HTTP reads are mocked."""
from contextlib import ExitStack, redirect_stderr, redirect_stdout
import ctypes
import io
import json
from pathlib import Path
import signal
import socket
import subprocess
import tempfile
import unittest
from unittest.mock import Mock, call, patch

from tools import run_reader_pilot as pilot


class LauncherTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="original pilot unit ")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.node = self.root / "Node with spaces" / "node"
        self.env = {"PATH": "existing-path"}
        self.output, self.errors = io.StringIO(), io.StringIO()
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.stack.enter_context(redirect_stdout(self.output))
        self.stack.enter_context(redirect_stderr(self.errors))

    def prepared_files(self):
        pilot.managed_venv(self.root, create=True)
        for path in (pilot.venv_python(self.root), self.root / "app/web/node_modules/vite/bin/vite.js",
                     self.root / "app/web/dist/index.html"):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("original unit fixture", encoding="utf-8")

    def fingerprint_files(self):
        for relative in ("requirements-extras/pilot-api.txt", "requirements-extras/symbolic.txt",
                         "app/web/package.json", "app/web/package-lock.json", "app/web/index.html",
                         "app/web/vite.config.ts", "app/web/tsconfig.json", "app/web/tsconfig.app.json",
                         "app/web/tsconfig.node.json", "app/web/dist/index.html", "app/web/src/App.tsx",
                         "app/web/scripts/prepare-pdf-assets.mjs", "app/web/public/licenses/original.txt"):
            path = self.root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("original test input " + relative, encoding="utf-8")
        (self.root / "requirements-extras/pilot-api.txt").write_text("fastapi==0.142.2 \\\n --hash=sha256:abc\n", encoding="utf-8")
        (self.root / "requirements-extras/symbolic.txt").write_text("sympy==1.14.0\n", encoding="utf-8")

    def original_responses(self):
        card = {"course_id": pilot.COURSE_ID, "book_id": pilot.BOOK_ID}
        return [{"library_id": pilot.LIBRARY_ID, "courses": [card]}, {"course": card}]

    def test_python_requires_cpython_313_only(self):
        for implementation, version, good in (("CPython", (3, 13, 0), True),
                                               ("CPython", (3, 13, 99), True),
                                               ("CPython", (3, 12, 10), False),
                                               ("CPython", (3, 14, 0), False),
                                               ("PyPy", (3, 13, 0), False)):
            with self.subTest(implementation=implementation, version=version), \
                    patch.object(pilot.platform, "python_implementation", return_value=implementation), \
                    patch.object(pilot.sys, "version_info", version):
                if good:
                    pilot.require_python()
                else:
                    with self.assertRaisesRegex(pilot.PilotError, "CPython 3.13"):
                        pilot.require_python()

    def test_node_accepts_only_supported_stable_major_22(self):
        for version, good in (("v22.20.0", True), ("v22.21.2", True), ("v22.19.9", False),
                               ("v24.20.0", False), ("v20.99.0", False),
                               ("v22.20.0-rc.1", False), ("22.20.0", False)):
            with self.subTest(version=version), patch.object(pilot.shutil, "which", return_value=str(self.node)), \
                    patch.object(pilot, "command_output", return_value=version) as output:
                if good:
                    self.assertEqual(pilot.resolve_node(self.root, self.env), self.node)
                else:
                    with self.assertRaises(pilot.PilotError):
                        pilot.resolve_node(self.root, self.env)
                self.assertEqual(output.call_args.args[0], [str(self.node), "--version"])

    def test_missing_node_and_shell_wrappers_are_rejected_without_execution(self):
        for candidate in (None, "C:/Node/node.cmd", "C:/Node/node.bat", "C:/Node/node.ps1"):
            with self.subTest(candidate=candidate), patch.object(pilot.shutil, "which", return_value=candidate), \
                    patch.object(pilot, "command_output") as output:
                with self.assertRaises(pilot.PilotError):
                    pilot.resolve_node(self.root, self.env)
                output.assert_not_called()

    def test_npm_cli_is_discovered_beside_node_without_running_cmd(self):
        cli = self.node.parent / "node_modules/npm/bin/npm-cli.js"
        cli.parent.mkdir(parents=True)
        cli.write_text("original fixture", encoding="utf-8")
        with patch.object(pilot, "WINDOWS", True), patch.object(pilot.shutil, "which", return_value="C:/npm.cmd"), \
                patch.object(pilot.subprocess, "run") as run:
            self.assertEqual(pilot.resolve_npm_cli(self.node), cli)
            run.assert_not_called()

    def test_npm_cli_resolves_a_posix_npm_symlink(self):
        cli = self.root / "npm distribution/bin/npm-cli.js"
        cli.parent.mkdir(parents=True)
        cli.write_text("original fixture", encoding="utf-8")
        wrapper = self.root / "npm"
        try:
            wrapper.symlink_to(cli)
        except OSError:
            self.skipTest("symlink creation is unavailable")
        with patch.object(pilot, "WINDOWS", False), patch.object(pilot.shutil, "which", return_value=str(wrapper)):
            self.assertEqual(pilot.resolve_npm_cli(self.node), cli)

    def test_missing_npm_reports_prerequisite_and_does_not_download(self):
        with patch.object(pilot.shutil, "which", return_value=None), patch.object(pilot.subprocess, "run") as run:
            with self.assertRaisesRegex(pilot.PilotError, "npm-cli.js"):
                pilot.resolve_npm_cli(self.node)
            run.assert_not_called()

    def test_runtime_probe_has_literal_argv_no_shell_bounded_timeout_and_no_bodies(self):
        argv = [str(self.root / "name with spaces & chars"), "--version"]
        result = Mock(returncode=0, stdout="v22.20.0\n")
        with patch.object(pilot.subprocess, "run", return_value=result) as run:
            self.assertEqual(pilot.command_output(argv, cwd=self.root, env=self.env), "v22.20.0")
        self.assertEqual(run.call_args.args[0], argv)
        self.assertIs(run.call_args.kwargs["shell"], False)
        self.assertEqual(run.call_args.kwargs["timeout"], 10)
        self.assertEqual(run.call_args.kwargs["stderr"], subprocess.DEVNULL)
        self.assertEqual(self.output.getvalue(), "")

    def test_probe_failures_hide_raw_output(self):
        for effect in (subprocess.TimeoutExpired(["original"], 10), OSError("private path")):
            with patch.object(pilot.subprocess, "run", side_effect=effect):
                with self.assertRaises(pilot.PilotError) as error:
                    pilot.command_output(["original"], cwd=self.root, env=self.env)
                self.assertNotIn("private path", str(error.exception))
        with patch.object(pilot.subprocess, "run", return_value=Mock(returncode=9, stdout="secret body")):
            with self.assertRaises(pilot.PilotError) as error:
                pilot.command_output(["original"], cwd=self.root, env=self.env)
            self.assertNotIn("secret body", str(error.exception))

    def test_managed_venv_requires_explicit_creation_and_can_retry_owned_setup(self):
        with self.assertRaisesRegex(pilot.PilotError, "--setup"):
            pilot.managed_venv(self.root)
        self.assertFalse((self.root / ".venv").exists())
        path = pilot.managed_venv(self.root, create=True)
        self.assertEqual(path, self.root / ".venv")
        self.assertEqual(pilot.managed_venv(self.root, create=True), path)

    def test_unrelated_venv_is_never_overwritten(self):
        directory = self.root / ".venv"
        directory.mkdir()
        sentinel = directory / "keep.txt"
        sentinel.write_text("unrelated environment", encoding="utf-8")
        with self.assertRaisesRegex(pilot.PilotError, "unrelated"):
            pilot.managed_venv(self.root, create=True)
        self.assertEqual(sentinel.read_text(encoding="utf-8"), "unrelated environment")
        self.assertFalse((directory / pilot.VENV_MARKER).exists())

    def test_venv_symlink_is_rejected(self):
        destination = self.root / "unrelated"
        destination.mkdir()
        try:
            (self.root / ".venv").symlink_to(destination, target_is_directory=True)
        except OSError:
            self.skipTest("symlink creation is unavailable")
        with self.assertRaisesRegex(pilot.PilotError, "symlink"):
            pilot.managed_venv(self.root, create=True)
        self.assertEqual(list(destination.iterdir()), [])

    def test_foreign_or_invalid_owner_marker_is_rejected(self):
        pilot.managed_venv(self.root, create=True)
        marker = self.root / ".venv" / pilot.VENV_MARKER
        for contents in ("not JSON", "{}", json.dumps({"purpose": "other"})):
            marker.write_text(contents, encoding="utf-8")
            with self.assertRaisesRegex(pilot.PilotError, "marker"):
                pilot.managed_venv(self.root, create=True)

    def test_venv_interpreter_path_does_not_resolve_to_global_python(self):
        target = self.root / "global-python"
        target.write_text("global", encoding="utf-8")
        with patch.object(pilot, "WINDOWS", False):
            local = pilot.venv_python(self.root)
            local.parent.mkdir(parents=True)
            try:
                local.symlink_to(target)
            except OSError:
                self.skipTest("symlink creation is unavailable")
            self.assertEqual(pilot.venv_python(self.root), self.root / ".venv/bin/python")
            self.assertNotEqual(pilot.venv_python(self.root), target)

    def test_environment_removes_real_user_book_and_runtime_overrides(self):
        values = {"BOOK_APP_DATA_DIR": "/real/progress", "BOOK_QA_API_KEY": "private",
                  "BOOK_QA_BASE_URL": "https://example.invalid", "PYTHONPATH": "/foreign",
                  "PYTHONHOME": "/other", "UVICORN_HOST": "0.0.0.0", "WEB_CONCURRENCY": "8",
                  "NODE_OPTIONS": "--require other.js", "NODE_PATH": "/foreign", "PATH": "keep"}
        with patch.dict(pilot.os.environ, values, clear=True):
            env = pilot.clean_environment()
        self.assertEqual(env["PATH"], "keep")
        for key in values.keys() - {"PATH"}:
            self.assertNotIn(key, env)
        self.assertEqual(env["PYTHONNOUSERSITE"], "1")

    def test_setup_uses_only_hash_locks_npm_ci_and_existing_build(self):
        self.prepared_files()
        owner = Mock()
        cli = self.root / "Node with spaces/npm-cli.js"
        with patch.object(pilot, "resolve_npm_cli", return_value=cli), \
                patch.object(pilot, "check_venv_python"), \
                patch.object(pilot, "save_prepared_setup"):
            pilot.setup(self.root, self.node, self.env, owner)
        commands = [entry.args[0] for entry in owner.run.call_args_list]
        self.assertEqual(len(commands), 5)
        self.assertEqual(commands[0], [pilot.sys.executable, "-m", "venv", "--copies", str(self.root / ".venv")])
        install = commands[1]
        self.assertEqual(install[:5], [str(pilot.venv_python(self.root)), "-m", "pip", "--isolated", "install"])
        self.assertIn("--require-hashes", install)
        self.assertIn("--only-binary=:all:", install)
        self.assertEqual([install[index + 1] for index, value in enumerate(install) if value == "-r"],
                         [str(self.root / "requirements-extras/pilot-api.txt"), str(self.root / "requirements-extras/symbolic.txt")])
        self.assertEqual(commands[2][-1], "check")
        self.assertEqual(commands[3], [str(self.node), str(cli), "ci", "--no-audit", "--no-fund"])
        self.assertEqual(commands[4], [str(self.node), str(cli), "run", "build"])
        self.assertTrue(all(entry.kwargs["env"]["PATH"].startswith(str(self.node.parent)) for entry in owner.run.call_args_list))
        self.assertNotIn("npx", " ".join(map(str, commands)))
        self.assertNotIn("playwright install", " ".join(map(str, commands)))

    def test_setup_creates_only_owned_project_local_venv(self):
        owner = Mock()
        with patch.object(pilot, "resolve_npm_cli", return_value=self.root / "npm-cli.js"), \
                patch.object(pilot, "check_venv_python"), \
                patch.object(pilot, "save_prepared_setup"):
            pilot.setup(self.root, self.node, self.env, owner)
        command = owner.run.call_args_list[0].args[0]
        self.assertEqual(command, [pilot.sys.executable, "-m", "venv", "--copies", str(self.root / ".venv")])
        self.assertTrue((self.root / ".venv" / pilot.VENV_MARKER).is_file())

    def test_setup_repairs_owned_partial_bootstrap_even_when_python_already_exists(self):
        self.prepared_files()
        self.assertTrue(pilot.venv_python(self.root).is_file())
        marker = (self.root / ".venv" / pilot.VENV_MARKER).read_bytes()
        owner = Mock()
        with patch.object(pilot, "resolve_npm_cli", return_value=self.root / "npm-cli.js"), \
                patch.object(pilot, "check_venv_python"), \
                patch.object(pilot, "save_prepared_setup"):
            pilot.setup(self.root, self.node, self.env, owner)
        bootstrap = owner.run.call_args_list[0].args[0]
        self.assertEqual(bootstrap, [pilot.sys.executable, "-m", "venv", "--copies", str(self.root / ".venv")])
        self.assertNotIn("--clear", bootstrap)
        self.assertEqual((self.root / ".venv" / pilot.VENV_MARKER).read_bytes(), marker)
        self.assertEqual(owner.run.call_args_list[1].args[0][2:5], ["pip", "--isolated", "install"])

    def test_setup_failure_stops_before_build_or_launch(self):
        self.prepared_files()
        owner = Mock()
        owner.run.side_effect = pilot.PilotError("install failed")
        with patch.object(pilot, "resolve_npm_cli", return_value=self.root / "npm-cli.js"), \
                patch.object(pilot, "check_venv_python"), \
                patch.object(pilot, "save_prepared_setup"):
            with self.assertRaisesRegex(pilot.PilotError, "install failed"):
                pilot.setup(self.root, self.node, self.env, owner)
        self.assertEqual(owner.run.call_count, 1)

    def test_installation_checks_local_prefix_and_python_version(self):
        self.prepared_files()
        for implementation, version, prefix, good in (("CPython", [3, 13], str(self.root / ".venv"), True),
                                                       ("CPython", [3, 12], str(self.root / ".venv"), False),
                                                       ("CPython", [3, 13], str(self.root), False),
                                                       ("PyPy", [3, 13], str(self.root / ".venv"), False)):
            with self.subTest(implementation=implementation, version=version, prefix=prefix), \
                    patch.object(pilot, "check_prepared_setup"), \
                    patch.object(pilot, "pinned_python_versions", return_value={}), \
                    patch.object(pilot, "command_output", return_value=json.dumps([implementation, version, prefix, {}])):
                if good:
                    pilot.check_installation(self.root, self.env)
                else:
                    with self.assertRaises(pilot.PilotError):
                        pilot.check_installation(self.root, self.env)

    def test_missing_build_does_not_install_or_spawn(self):
        self.prepared_files()
        (self.root / "app/web/dist/index.html").unlink()
        with patch.object(pilot.subprocess, "Popen") as popen, patch.object(pilot, "setup") as setup:
            with self.assertRaisesRegex(pilot.PilotError, "--setup"):
                pilot.check_installation(self.root, self.env)
        popen.assert_not_called()
        setup.assert_not_called()

    def test_reserves_both_loopback_ports_and_closes_after_use(self):
        sockets = [Mock(), Mock()]
        with patch.object(pilot, "WINDOWS", False), patch.object(pilot.socket, "socket", side_effect=sockets):
            with pilot.reserve_ports() as reserved:
                self.assertEqual(set(reserved), {8000, 5173})
                for sock, port in zip(sockets, (8000, 5173)):
                    sock.close.assert_not_called()
                    self.assertEqual(sock.method_calls, [
                        call.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1),
                        call.bind(("127.0.0.1", port)), call.listen(1),
                    ])
        for sock in sockets:
            sock.setsockopt.assert_called_once_with(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sockets[0].bind.assert_called_once_with(("127.0.0.1", 8000))
        sockets[1].bind.assert_called_once_with(("127.0.0.1", 5173))
        for sock in sockets:
            sock.close.assert_called_once()

    def test_occupied_port_closes_reservations_without_any_process(self):
        for index in (0, 1):
            sockets = [Mock(), Mock()]
            sockets[index].bind.side_effect = OSError("in use")
            with self.subTest(index=index), patch.object(pilot, "WINDOWS", False), \
                    patch.object(pilot.socket, "socket", side_effect=sockets), \
                    patch.object(pilot.subprocess, "Popen") as popen:
                with self.assertRaisesRegex(pilot.PilotError, "already in use"):
                    with pilot.reserve_ports():
                        self.fail("occupied port must not yield")
                popen.assert_not_called()
                for sock in sockets[:index + 1]:
                    sock.close.assert_called_once()

    def test_windows_reservation_uses_exclusive_bind(self):
        sockets = [Mock(), Mock()]
        with patch.object(pilot, "WINDOWS", True), patch.object(pilot.socket, "SO_EXCLUSIVEADDRUSE", -5, create=True), \
                patch.object(pilot.socket, "socket", side_effect=sockets):
            with pilot.reserve_ports():
                pass
        for sock in sockets:
            sock.setsockopt.assert_called_once_with(socket.SOL_SOCKET, -5, 1)
            sock.listen.assert_called_once_with(1)

    def test_listen_failure_releases_reservations_before_setup(self):
        sockets = [Mock(), Mock()]
        sockets[1].listen.side_effect = OSError("competing reservation")
        with patch.object(pilot, "WINDOWS", False), \
                patch.object(pilot.socket, "socket", side_effect=sockets), \
                patch.object(pilot, "setup") as setup:
            with self.assertRaisesRegex(pilot.PilotError, "already in use"):
                with pilot.reserve_ports():
                    setup()
            setup.assert_not_called()
        for sock in sockets:
            sock.close.assert_called_once()

    def test_posix_children_use_fresh_sessions_and_literal_arguments(self):
        process = Mock(pid=4321)
        owner = pilot.ProcessOwner(pilot.StopRequest())
        command = [str(self.root / "literal & spaced Python"), "-m", "uvicorn", pilot.API_FACTORY]
        with patch.object(pilot, "WINDOWS", False), patch.object(pilot.subprocess, "Popen", return_value=process) as popen:
            child = owner.start(command, cwd=self.root, env=self.env, label="original")
        self.assertEqual(child.process, process)
        self.assertEqual(owner.children, [child])
        self.assertEqual(popen.call_args.args[0], command)
        self.assertIs(popen.call_args.kwargs["shell"], False)
        self.assertIs(popen.call_args.kwargs["start_new_session"], True)
        self.assertEqual(popen.call_args.kwargs["stdout"], subprocess.DEVNULL)
        self.assertEqual(popen.call_args.kwargs["stderr"], subprocess.DEVNULL)

    def test_windows_children_are_suspended_until_owned_job_assignment(self):
        process, job = Mock(pid=4321), Mock()
        events = []
        owner = pilot.ProcessOwner(pilot.StopRequest())
        def popen(*args, **kwargs):
            events.append("suspended")
            self.assertEqual(kwargs["creationflags"], 0x204)
            self.assertIs(kwargs["shell"], False)
            return process
        job.assign_and_resume.side_effect = lambda child: events.append("owned_then_resumed")
        with patch.object(pilot, "WINDOWS", True), patch.object(pilot, "WindowsJob", return_value=job), \
                patch.object(pilot.subprocess, "Popen", side_effect=popen):
            child = owner.start(["node.exe", "literal path/vite.js"], cwd=self.root, env=self.env, label="preview")
        self.assertEqual(events, ["suspended", "owned_then_resumed"])
        self.assertTrue(child.resumed)
        job.assign_and_resume.assert_called_once_with(process)

    def test_windows_job_failure_kills_only_the_suspended_child_and_fails_closed(self):
        process = Mock(pid=4321)
        process.poll.return_value = None
        job = Mock()
        job.assign_and_resume.side_effect = pilot.PilotError("nested job rejected")
        owner = pilot.ProcessOwner(pilot.StopRequest())
        with patch.object(pilot, "WINDOWS", True), patch.object(pilot, "WindowsJob", return_value=job), \
                patch.object(pilot.subprocess, "Popen", return_value=process):
            with self.assertRaisesRegex(pilot.PilotError, "nested job"):
                owner.start(["node.exe"], cwd=self.root, env=self.env, label="preview")
        process.kill.assert_called_once()
        process.wait.assert_called_once_with(timeout=pilot.FORCE_TIMEOUT)
        job.close.assert_called_once()
        self.assertEqual(owner.children, [])

    def test_spawn_failure_closes_new_windows_job(self):
        job = Mock()
        owner = pilot.ProcessOwner(pilot.StopRequest())
        with patch.object(pilot, "WINDOWS", True), patch.object(pilot, "WindowsJob", return_value=job), \
                patch.object(pilot.subprocess, "Popen", side_effect=OSError("private path")):
            with self.assertRaisesRegex(pilot.PilotError, "Could not start preview"):
                owner.start(["node.exe"], cwd=self.root, env=self.env, label="preview")
        job.close.assert_called_once()
        self.assertEqual(owner.children, [])

    def test_child_failure_is_reported_before_readiness_is_accepted(self):
        owner = pilot.ProcessOwner(pilot.StopRequest())
        owner.children = [pilot.OwnedChild(Mock(poll=Mock(return_value=7)), "original API")]
        with self.assertRaisesRegex(pilot.PilotError, "exit 7"):
            owner.assert_running()

    def test_posix_cleanup_targets_owned_group_even_after_leader_exit(self):
        process = Mock(pid=9876, poll=Mock(return_value=0))
        child = pilot.OwnedChild(process, "original API")
        with (patch.object(pilot.os, "killpg", create=True) as killpg,
              patch.object(pilot.signal, "SIGKILL", 9, create=True)):
            self.assertTrue(child.alive())
            child.graceful()
            child.force()
        self.assertEqual(killpg.call_args_list, [call(9876, 0), call(9876, signal.SIGTERM), call(9876, 9)])
        process.terminate.assert_not_called()
        process.kill.assert_not_called()

    def test_windows_cleanup_uses_ctrl_break_then_owned_tree_not_terminate(self):
        process, job = Mock(pid=9876), Mock()
        child = pilot.OwnedChild(process, "original API", job)
        with patch.object(pilot.signal, "CTRL_BREAK_EVENT", 1, create=True), patch.object(pilot.os, "kill") as kill:
            child.graceful()
            child.force()
        kill.assert_called_once_with(9876, 1)
        job.force.assert_called_once()
        process.terminate.assert_not_called()

    def test_graceful_cleanup_reaps_owned_children_and_is_idempotent(self):
        child = Mock(job=Mock())
        child.alive.side_effect = [True, False]
        owner = pilot.ProcessOwner(pilot.StopRequest())
        owner.children = [child]
        with patch.object(pilot.time, "sleep"):
            owner.stop_children()
            owner.stop_children()
        child.graceful.assert_called_once()
        child.force.assert_not_called()
        child.process.wait.assert_called_once_with(timeout=pilot.FORCE_TIMEOUT)
        child.job.close.assert_called_once()
        self.assertEqual(owner.children, [])

    def test_cleanup_forces_owned_tree_after_bounded_grace_period(self):
        child = Mock(job=Mock())
        child.alive.side_effect = [True, False]
        owner = pilot.ProcessOwner(pilot.StopRequest())
        owner.children = [child]
        with patch.object(pilot.time, "monotonic", side_effect=[0, 0, 6, 6, 6]), \
                patch.object(pilot.time, "sleep"):
            owner.stop_children()
        child.graceful.assert_called_once()
        child.force.assert_called_once()
        child.job.close.assert_called_once()

    def test_failed_cleanup_is_honest_and_retains_ownership(self):
        child = Mock(job=Mock(), alive=Mock(return_value=True))
        owner = pilot.ProcessOwner(pilot.StopRequest())
        owner.children = [child]
        with patch.object(pilot.time, "monotonic", side_effect=[0, 6, 6, 12]):
            with self.assertRaisesRegex(pilot.PilotError, "could not be confirmed"):
                owner.stop_children()
        self.assertEqual(owner.children, [child])
        child.job.close.assert_not_called()

    def test_repeated_interrupt_is_recorded_without_interrupting_ownership(self):
        stop = pilot.StopRequest()
        stop.handle(signal.SIGINT, None)
        stop.handle(signal.SIGTERM, None)
        with self.assertRaises(pilot.PilotInterrupted):
            stop.check()
        owner = pilot.ProcessOwner(stop)
        with patch.object(pilot.subprocess, "Popen") as popen:
            with self.assertRaises(pilot.PilotInterrupted):
                owner.start(["never"], cwd=self.root, env=self.env, label="never")
            popen.assert_not_called()

    def test_signal_handlers_are_installed_and_restored_including_sigbreak(self):
        with patch.object(pilot.signal, "SIGBREAK", 21, create=True), \
                patch.object(pilot.signal, "signal", return_value="prior") as install:
            stop = pilot.StopRequest()
            with pilot.handle_signals(stop):
                self.assertEqual(install.call_count, 3)
        self.assertEqual(install.call_count, 6)
        self.assertEqual(install.call_args_list[-1], call(21, "prior"))

    def test_http_checks_exact_original_library_course_and_book(self):
        good = self.original_responses()
        with patch.object(pilot, "read_response", side_effect=[json.dumps(value) for value in good]) as read:
            self.assertTrue(pilot.original_ready(Mock(), "http://127.0.0.1:8000", 1))
        self.assertEqual(read.call_args_list[1].args[1], "http://127.0.0.1:8000/api/courses/original_algebra_pilot")
        for body in ({"library_id": "canonical", "courses": []},
                     {"library_id": pilot.LIBRARY_ID, "courses": []},
                     {"library_id": pilot.LIBRARY_ID, "courses": [{"course_id": "other", "book_id": pilot.BOOK_ID}]},
                     {"library_id": pilot.LIBRARY_ID, "courses": good[0]["courses"] * 2}, []):
            with patch.object(pilot, "read_response", return_value=json.dumps(body)):
                self.assertFalse(pilot.original_ready(Mock(), "http://127.0.0.1:8000", 1))

    def test_original_course_endpoint_cannot_return_a_different_book(self):
        library = self.original_responses()[0]
        course = {"course": {"course_id": pilot.COURSE_ID, "book_id": "canonical_book"}}
        with patch.object(pilot, "read_response", side_effect=[json.dumps(library), json.dumps(course)]):
            self.assertFalse(pilot.original_ready(Mock(), "http://127.0.0.1:8000", 1))

    def test_http_body_is_bounded_and_never_printed(self):
        response = Mock(status=200)
        response.read.return_value = b"x" * (pilot.MAX_RESPONSE + 1)
        opener = Mock()
        opener.open.return_value.__enter__ = Mock(return_value=response)
        opener.open.return_value.__exit__ = Mock(return_value=False)
        with self.assertRaises(ValueError):
            pilot.read_response(opener, "http://127.0.0.1:8000/api/library", 0.5)
        response.read.assert_called_once_with(pilot.MAX_RESPONSE + 1)
        self.assertEqual(self.output.getvalue(), "")

    def test_readiness_is_proxy_free_checks_frontend_proxy_and_checks_children_twice(self):
        owner, opener = Mock(spec=pilot.ProcessOwner), Mock()
        with patch.object(pilot.urllib.request, "build_opener", return_value=opener) as build, \
                patch.object(pilot, "original_ready", return_value=True) as original, \
                patch.object(pilot, "read_response", return_value=b"original html") as read:
            pilot.wait_ready(owner, web=True)
        self.assertEqual(build.call_args.args[0].proxies, {})
        self.assertIsInstance(build.call_args.args[1], pilot.NoRedirect)
        self.assertEqual(original.call_args.args[1], "http://127.0.0.1:5173")
        self.assertEqual(read.call_args.args[1], "http://127.0.0.1:5173/")
        self.assertEqual(owner.assert_running.call_count, 2)
        self.assertEqual(self.output.getvalue(), "")

    def test_readiness_rejects_redirects(self):
        self.assertIsNone(pilot.NoRedirect().redirect_request(None, None, 302, "redirect", {}, "https://example.invalid"))

    def test_readiness_timeout_is_bounded_and_does_not_disclose_response(self):
        with patch.object(pilot.time, "monotonic", side_effect=[0, 0, 0, 2]), \
                patch.object(pilot.time, "sleep"), \
                patch.object(pilot, "original_ready", side_effect=ValueError("private response")):
            with self.assertRaisesRegex(pilot.PilotError, "did not become ready") as error:
                pilot.wait_ready(Mock(spec=pilot.ProcessOwner), timeout=1)
        self.assertNotIn("private response", str(error.exception))

    def test_launch_uses_only_original_direct_commands_with_isolated_temp_data(self):
        owner = Mock()
        reservations = {8000: Mock(), 5173: Mock()}
        events = []
        captured = {}
        def start(argv, **kwargs):
            events.append("api" if len(events) == 0 else "web")
            if "uvicorn" in argv:
                captured.update(kwargs["env"])
                temp = Path(captured["TMP"])
                (temp / "original fixture.txt").write_text("temporary", encoding="utf-8")
            return Mock()
        def ready(_owner, **kwargs):
            events.append("web ready" if kwargs.get("web") else "api ready")
        def stop():
            events.append("stopped")
            self.assertTrue((Path(captured["TMP"]) / "original fixture.txt").exists())
        owner.start.side_effect, owner.stop_children.side_effect = start, stop
        with patch.object(pilot, "wait_ready", side_effect=ready):
            pilot.launch(self.root, self.node, self.env, owner, reservations, check=True)
        self.assertEqual(events, ["api", "api ready", "web", "web ready", "stopped"])
        commands = [entry.args[0] for entry in owner.start.call_args_list]
        self.assertEqual(commands[0], [str(pilot.venv_python(self.root)), "-m", "uvicorn", pilot.API_FACTORY,
                                      "--factory", "--host", "127.0.0.1", "--port", "8000", "--workers", "1", "--no-access-log"])
        self.assertEqual(commands[1], [str(self.node), str(self.root / "app/web/node_modules/vite/bin/vite.js"),
                                      "preview", "--host", "127.0.0.1", "--port", "5173", "--strictPort"])
        self.assertEqual(captured["TMP"], captured["TEMP"])
        self.assertEqual(captured["TMP"], captured["TMPDIR"])
        self.assertEqual(Path(captured["BOOK_APP_DATA_DIR"]), Path(captured["TMP"]) / "app-data")
        self.assertFalse(Path(captured["TMP"]).exists())
        for forbidden in ("app.api.main:app", "npm.cmd", "npx", "--reload", "--open"):
            self.assertNotIn(forbidden, " ".join(map(str, commands)))
        reservations[8000].close.assert_called_once()
        reservations[5173].close.assert_called_once()

    def test_partial_start_failure_stops_api_before_removing_parent_temp_files(self):
        owner, captured = Mock(), {}
        def start(argv, **kwargs):
            if captured:
                raise pilot.PilotError("preview failed")
            captured.update(kwargs["env"])
            (Path(captured["TMP"]) / "fixture").write_text("original", encoding="utf-8")
        owner.start.side_effect = start
        owner.stop_children.side_effect = lambda: self.assertTrue((Path(captured["TMP"]) / "fixture").exists())
        with patch.object(pilot, "wait_ready"):
            with self.assertRaisesRegex(pilot.PilotError, "preview failed"):
                pilot.launch(self.root, self.node, self.env, owner, {8000: Mock(), 5173: Mock()}, check=True)
        owner.stop_children.assert_called_once()
        self.assertFalse(Path(captured["TMP"]).exists())

    def test_api_readiness_failure_never_starts_frontend(self):
        owner = Mock()
        with patch.object(pilot, "wait_ready", side_effect=pilot.PilotError("API timeout")):
            with self.assertRaisesRegex(pilot.PilotError, "API timeout"):
                pilot.launch(self.root, self.node, self.env, owner, {8000: Mock(), 5173: Mock()}, check=True)
        self.assertEqual(owner.start.call_count, 1)
        owner.stop_children.assert_called_once()

    def test_default_launch_remains_alive_until_interrupt_and_cleans_up(self):
        owner = Mock()
        owner.assert_running = Mock(side_effect=pilot.PilotInterrupted())
        with patch.object(pilot, "wait_ready"), patch.object(pilot.time, "sleep"):
            with self.assertRaises(pilot.PilotInterrupted):
                pilot.launch(self.root, self.node, self.env, owner, {8000: Mock(), 5173: Mock()})
        owner.assert_running.assert_called_once()
        owner.stop_children.assert_called_once()
        self.assertIn("Ctrl+C", self.output.getvalue())

    def test_uncertain_process_cleanup_retains_temp_data_and_never_claims_success(self):
        owner = Mock()
        owner.stop_children.side_effect = pilot.PilotError("owned tree still alive")
        captured = {}
        def start(argv, **kwargs):
            if "uvicorn" in argv:
                captured.update(kwargs["env"])
        owner.start.side_effect = start
        with patch.object(pilot, "wait_ready"):
            with self.assertRaisesRegex(pilot.PilotError, "still alive"):
                pilot.launch(self.root, self.node, self.env, owner, {8000: Mock(), 5173: Mock()}, check=True)
        retained = Path(captured["TMP"])
        self.addCleanup(lambda: pilot.shutil.rmtree(retained, ignore_errors=True))
        self.assertTrue(retained.is_dir())
        self.assertIn("Cleanup is incomplete", self.errors.getvalue())
        self.assertNotIn("temporary data removed", self.output.getvalue())

    def main_mocks(self):
        stack = ExitStack()
        self.addCleanup(stack.close)
        mocks = {}
        for name in ("require_python", "resolve_node", "check_installation", "setup", "launch"):
            mocks[name] = stack.enter_context(patch.object(pilot, name))
        mocks["resolve_node"].return_value = self.node
        stack.enter_context(patch.object(pilot, "ROOT", self.root))
        stack.enter_context(patch.object(pilot, "WINDOWS", False))
        stack.enter_context(patch.object(pilot.socket, "socket", side_effect=[Mock(), Mock()]))
        mocks["owner"] = stack.enter_context(patch.object(pilot, "ProcessOwner")).return_value
        return mocks

    def test_default_main_never_sets_up_or_downloads(self):
        mocks = self.main_mocks()
        self.assertEqual(pilot.main([]), 0)
        mocks["setup"].assert_not_called()
        mocks["launch"].assert_called_once()
        self.assertIs(mocks["launch"].call_args.kwargs["check"], False)

    def test_explicit_setup_check_prepares_then_launches_and_exits(self):
        mocks = self.main_mocks()
        events = []
        mocks["setup"].side_effect = lambda *args: events.append("setup")
        mocks["check_installation"].side_effect = lambda *args: events.append("installation")
        mocks["launch"].side_effect = lambda *args, **kwargs: events.append("launch")
        self.assertEqual(pilot.main(["--setup", "--check"]), 0)
        self.assertEqual(events, ["setup", "installation", "launch"])
        self.assertIs(mocks["launch"].call_args.kwargs["check"], True)
        mocks["owner"].stop_children.assert_called_once()

    def test_main_setup_failure_cleans_owned_children(self):
        mocks = self.main_mocks()
        mocks["setup"].side_effect = pilot.PilotError("setup failed")
        self.assertEqual(pilot.main(["--setup"]), 1)
        mocks["owner"].stop_children.assert_called_once()
        mocks["launch"].assert_not_called()

    def test_main_cleanup_failure_overrides_success_or_interrupt(self):
        for interrupt in (False, True):
            with self.subTest(interrupt=interrupt):
                mocks = self.main_mocks()
                if interrupt:
                    mocks["launch"].side_effect = pilot.PilotInterrupted()
                mocks["owner"].stop_children.side_effect = pilot.PilotError("cleanup incomplete")
                self.assertEqual(pilot.main([]), 1)
        self.assertNotIn("Original reader stopped.", self.output.getvalue())

    def test_main_occupied_port_prevents_runtime_probes_and_setup(self):
        mocks = self.main_mocks()
        busy = Mock()
        busy.bind.side_effect = OSError("busy")
        with patch.object(pilot.socket, "socket", return_value=busy):
            self.assertEqual(pilot.main(["--setup"]), 1)
        mocks["resolve_node"].assert_not_called()
        mocks["setup"].assert_not_called()
        mocks["launch"].assert_not_called()

    def test_main_rejects_unsupported_python_before_any_process(self):
        with patch.object(pilot.sys, "version_info", (3, 12, 0)), \
                patch.object(pilot.subprocess, "Popen") as popen, \
                patch.object(pilot.subprocess, "run") as run:
            self.assertEqual(pilot.main([]), 1)
        popen.assert_not_called()
        run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
