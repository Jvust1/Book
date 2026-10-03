"""One-command, loopback-only launch of the original synthetic reader pilot.

The default never installs anything. --setup explicitly creates the owned .venv,
installs the existing locks and builds the web app before launching. --check runs
real readiness checks and then shuts down. Only the Python standard library is
needed to run this launcher or its unit tests.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
WINDOWS = os.name == "nt"
HOST = "127.0.0.1"
API_PORT, WEB_PORT = 8000, 5173
API_FACTORY = "app_tests.synthetic_pilot_server:create_app"
LIBRARY_ID = "original_pilot_library"
COURSE_ID = "original_algebra_pilot"
BOOK_ID = "original_algebra_book"
VENV_MARKER = ".reader-pilot-owner.json"
PREPARED_MARKER = ".reader-pilot-prepared.json"
STARTUP_TIMEOUT = 60.0
STOP_TIMEOUT = 5.0
FORCE_TIMEOUT = 5.0
POLL_INTERVAL = 0.1
MAX_RESPONSE = 64 * 1024


class PilotError(Exception):
    """A concise, safe-to-display launcher error, never an HTTP response body."""


class PilotInterrupted(Exception):
    pass


class StopRequest:
    def __init__(self):
        self.requested = False

    def handle(self, _signum, _frame):
        # Do not raise asynchronously between Popen and recording ownership, or
        # during shutdown. Repeated interrupts remain harmless and idempotent.
        self.requested = True

    def check(self):
        if self.requested:
            raise PilotInterrupted()


@contextmanager
def handle_signals(stop):
    previous = {}
    for name in ("SIGINT", "SIGTERM", "SIGBREAK"):
        value = getattr(signal, name, None)
        if value is not None:
            previous[value] = signal.signal(value, stop.handle)
    try:
        yield
    finally:
        for value, handler in previous.items():
            signal.signal(value, handler)


def require_python():
    if platform.python_implementation() != "CPython" or sys.version_info[:2] != (3, 13):
        raise PilotError("CPython 3.13.x is required. Install it, then use python tools/run_reader_pilot.py --setup.")


def clean_environment():
    env = os.environ.copy()
    for key in list(env):
        if (key.upper().startswith(("BOOK_", "UVICORN_")) or key.upper() in {
            "PYTHONPATH", "PYTHONHOME", "PYTHONSTARTUP", "PYTHONINSPECT", "PYTHONUSERBASE",
            "NODE_OPTIONS", "NODE_PATH", "WEB_CONCURRENCY",
        }):
            del env[key]
    env["PYTHONNOUSERSITE"] = "1"
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    return env


def command_output(argv, *, cwd, env):
    """Bounded read-only runtime probes; never shell wrappers or installers."""
    try:
        result = subprocess.run(argv, cwd=cwd, env=env, shell=False,
                                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                stderr=subprocess.DEVNULL, text=True, encoding="utf-8",
                                timeout=10, check=False)
    except (OSError, subprocess.TimeoutExpired):
        raise PilotError("A required runtime could not be checked. Verify Python 3.13 and Node 22.20+ (major 22).") from None
    if result.returncode != 0:
        raise PilotError("A runtime check failed. Run python tools/run_reader_pilot.py --setup after checking prerequisites.")
    return result.stdout.strip()


def resolve_node(root, env):
    found = shutil.which("node.exe" if WINDOWS else "node")
    if not found or Path(found).suffix.lower() in (".cmd", ".bat", ".ps1"):
        raise PilotError("Node.js 22.20+ within major 22 is required on PATH; install the official Node 22 distribution.")
    node = Path(found).resolve()
    version = command_output([str(node), "--version"], cwd=root, env=env)
    match = re.fullmatch(r"v(\d+)\.(\d+)\.(\d+)", version)
    if not match or tuple(map(int, match.groups())) < (22, 20, 0) or int(match.group(1)) != 22:
        raise PilotError("Node.js 22.20+ within major 22 is required; Node 20, 24 and prereleases are not supported.")
    return node


def resolve_npm_cli(node):
    """Run npm's JS entry point via Node, never npm.cmd or a shell string."""
    candidates = [node.parent / "node_modules/npm/bin/npm-cli.js",
                  node.parent.parent / "lib/node_modules/npm/bin/npm-cli.js"]
    wrapper = shutil.which("npm.cmd" if WINDOWS else "npm")
    if wrapper:
        path = Path(wrapper)
        if not WINDOWS:
            resolved = path.resolve()
            if resolved.name == "npm-cli.js":
                candidates.append(resolved)
        candidates.append(path.parent / "node_modules/npm/bin/npm-cli.js")
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    raise PilotError("npm-cli.js was not found. Install the official Node 22 distribution, including npm, then retry --setup.")


def venv_python(root):
    # Do not resolve this path: POSIX virtualenv Python may be a symlink, and
    # resolving it would silently run the global interpreter outside the venv.
    return root / ".venv" / ("Scripts/python.exe" if WINDOWS else "bin/python")


def managed_venv(root, *, create=False):
    directory = root / ".venv"
    marker = directory / VENV_MARKER
    expected = {"purpose": "book-original-reader-pilot", "version": 1, "root": str(root)}
    if directory.is_symlink() or (hasattr(directory, "is_junction") and directory.is_junction()):
        raise PilotError("Refusing a symlink or junction at .venv. Choose a clean project directory.")
    if not directory.exists():
        if not create:
            raise PilotError("The pilot is not set up. Run python tools/run_reader_pilot.py --setup once.")
        directory.mkdir()  # Exclusive creation; never clear or replace an existing directory.
        marker.write_text(json.dumps(expected), encoding="utf-8")
    if not directory.is_dir() or marker.is_symlink() or not marker.is_file():
        raise PilotError("Refusing an unrelated .venv. Move it yourself or use a clean project directory.")
    try:
        data = marker.read_text(encoding="utf-8")
        if len(data) > 4096 or json.loads(data) != expected:
            raise ValueError()
    except (OSError, ValueError):
        raise PilotError("The .venv ownership marker does not match this project. Use a clean project directory.") from None
    return directory


def pinned_python_versions(root):
    expected = {}
    for name in ("pilot-api.txt", "symbolic.txt"):
        for raw in (root / "requirements-extras" / name).read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith(("#", "--hash=")):
                continue
            match = re.fullmatch(r"([A-Za-z0-9][A-Za-z0-9._-]*)==([A-Za-z0-9][A-Za-z0-9.!+_-]*)\s*\\?", line)
            if not match or (match.group(1) in expected and expected[match.group(1)] != match.group(2)):
                raise PilotError("The pilot Python locks must contain exact package pins and hashes.")
            expected[match.group(1)] = match.group(2)
    if not expected:
        raise PilotError("The pilot Python dependency locks are empty.")
    return expected


def setup_fingerprint(root):
    """Detect stale source/locks and changed or missing build output, not secrets.

    Generated PDF assets are derived from package-lock.json; they are not input
    files. Their built copies are covered by the complete dist fingerprint.
    No file contents or environment values are included in the saved marker.
    """
    web = root / "app/web"
    files = {root / "requirements-extras/pilot-api.txt", root / "requirements-extras/symbolic.txt",
             web / "package.json", web / "package-lock.json", web / "index.html", web / "vite.config.ts",
             web / "tsconfig.json", web / "tsconfig.app.json", web / "tsconfig.node.json", web / "dist/index.html"}
    for directory in ("src", "scripts", "public", "dist"):
        for path in (web / directory).rglob("*"):
            if path.is_file() and not (directory == "public" and path.is_relative_to(web / "public/pdfjs")):
                files.add(path)
    for name in (".env", ".env.local", ".env.production", ".env.production.local"):
        if (web / name).exists():
            files.add(web / name)
    digest = hashlib.sha256()
    for path in sorted(files, key=lambda item: item.relative_to(root).as_posix()):
        if not path.is_file():
            raise PilotError("The pilot build is incomplete. Run python tools/run_reader_pilot.py --setup.")
        digest.update(path.relative_to(root).as_posix().encode("utf-8") + b"\0")
        with path.open("rb") as stream:
            while block := stream.read(128 * 1024):
                digest.update(block)
        digest.update(b"\0")
    return digest.hexdigest()


def save_prepared_setup(root):
    marker = root / ".venv" / PREPARED_MARKER
    marker.write_text(json.dumps({"version": 1, "fingerprint": setup_fingerprint(root)}), encoding="utf-8")


def check_prepared_setup(root):
    marker = root / ".venv" / PREPARED_MARKER
    try:
        if marker.is_symlink() or not marker.is_file():
            raise ValueError()
        saved = json.loads(marker.read_text(encoding="utf-8"))
        if saved != {"version": 1, "fingerprint": setup_fingerprint(root)}:
            raise ValueError()
    except (OSError, ValueError):
        raise PilotError("The pilot setup is missing or stale. Run python tools/run_reader_pilot.py --setup; ordinary launch never rebuilds or installs.") from None


class WindowsJob:
    """Own exactly one suspended process and its future descendants.

    CreateProcess starts suspended so the Windows venv redirector cannot spawn
    its interpreter before job assignment. A kill-on-close job covers all
    descendants, even when the initial process has already exited. Nested jobs
    work on supported Windows runners; assignment failure is a hard failure.
    """
    def __init__(self):
        import ctypes
        from ctypes import wintypes

        class BasicLimit(ctypes.Structure):
            _fields_ = [("PerProcessUserTimeLimit", ctypes.c_longlong),
                        ("PerJobUserTimeLimit", ctypes.c_longlong),
                        ("LimitFlags", wintypes.DWORD),
                        ("MinimumWorkingSetSize", ctypes.c_size_t),
                        ("MaximumWorkingSetSize", ctypes.c_size_t),
                        ("ActiveProcessLimit", wintypes.DWORD),
                        ("Affinity", ctypes.c_size_t),
                        ("PriorityClass", wintypes.DWORD), ("SchedulingClass", wintypes.DWORD)]

        class IOCount(ctypes.Structure):
            _fields_ = [(name, ctypes.c_ulonglong) for name in (
                "ReadOperationCount", "WriteOperationCount", "OtherOperationCount",
                "ReadTransferCount", "WriteTransferCount", "OtherTransferCount")]

        class ExtendedLimit(ctypes.Structure):
            _fields_ = [("BasicLimitInformation", BasicLimit), ("IoInfo", IOCount),
                        ("ProcessMemoryLimit", ctypes.c_size_t), ("JobMemoryLimit", ctypes.c_size_t),
                        ("PeakProcessMemoryUsed", ctypes.c_size_t), ("PeakJobMemoryUsed", ctypes.c_size_t)]

        class Accounting(ctypes.Structure):
            _fields_ = [(name, ctypes.c_longlong) for name in (
                "TotalUserTime", "TotalKernelTime", "ThisPeriodTotalUserTime", "ThisPeriodTotalKernelTime")] + [
                (name, wintypes.DWORD) for name in (
                    "TotalPageFaultCount", "TotalProcesses", "ActiveProcesses", "TotalTerminatedProcesses")]

        class ThreadEntry(ctypes.Structure):
            _fields_ = [("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD),
                        ("th32ThreadID", wintypes.DWORD), ("th32OwnerProcessID", wintypes.DWORD),
                        ("tpBasePri", wintypes.LONG), ("tpDeltaPri", wintypes.LONG), ("dwFlags", wintypes.DWORD)]

        self.ctypes, self.Accounting, self.ThreadEntry = ctypes, Accounting, ThreadEntry
        api = self.api = ctypes.WinDLL("kernel32", use_last_error=True)
        signatures = {
            "CreateJobObjectW": ([wintypes.LPVOID, wintypes.LPCWSTR], wintypes.HANDLE),
            "SetInformationJobObject": ([wintypes.HANDLE, ctypes.c_int, wintypes.LPVOID, wintypes.DWORD], wintypes.BOOL),
            "QueryInformationJobObject": ([wintypes.HANDLE, ctypes.c_int, wintypes.LPVOID, wintypes.DWORD, wintypes.LPVOID], wintypes.BOOL),
            "AssignProcessToJobObject": ([wintypes.HANDLE, wintypes.HANDLE], wintypes.BOOL),
            "TerminateJobObject": ([wintypes.HANDLE, wintypes.UINT], wintypes.BOOL),
            "CloseHandle": ([wintypes.HANDLE], wintypes.BOOL),
            "CreateToolhelp32Snapshot": ([wintypes.DWORD, wintypes.DWORD], wintypes.HANDLE),
            "Thread32First": ([wintypes.HANDLE, ctypes.POINTER(ThreadEntry)], wintypes.BOOL),
            "Thread32Next": ([wintypes.HANDLE, ctypes.POINTER(ThreadEntry)], wintypes.BOOL),
            "OpenThread": ([wintypes.DWORD, wintypes.BOOL, wintypes.DWORD], wintypes.HANDLE),
            "ResumeThread": ([wintypes.HANDLE], wintypes.DWORD),
        }
        for name, (args, result) in signatures.items():
            function = getattr(api, name)
            function.argtypes, function.restype = args, result
        self.handle = api.CreateJobObjectW(None, None)
        if not self.handle:
            raise PilotError("Windows could not create an owned process job; no servers were started.")
        limits = ExtendedLimit()
        limits.BasicLimitInformation.LimitFlags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not api.SetInformationJobObject(self.handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)):
            self.close()
            raise PilotError("Windows could not configure owned process cleanup; no servers were started.")

    def assign_and_resume(self, process):
        if not self.api.AssignProcessToJobObject(self.handle, int(process._handle)):
            raise PilotError("Windows refused the owned process job. The suspended child will be stopped; no fallback server is used.")
        # Popen closes the primary thread handle. Find that still-suspended
        # thread by its exact owner PID using the documented Toolhelp APIs.
        c = self.ctypes
        snapshot = self.api.CreateToolhelp32Snapshot(0x4, 0)  # TH32CS_SNAPTHREAD
        if snapshot == c.c_void_p(-1).value:
            raise PilotError("Windows could not resume the owned child process.")
        try:
            entry = self.ThreadEntry()
            entry.dwSize = c.sizeof(entry)
            present = self.api.Thread32First(snapshot, c.byref(entry))
            while present:
                if entry.th32OwnerProcessID == process.pid:
                    thread = self.api.OpenThread(0x2, False, entry.th32ThreadID)  # THREAD_SUSPEND_RESUME
                    if not thread:
                        break
                    try:
                        if self.api.ResumeThread(thread) != 0xFFFFFFFF:
                            return
                    finally:
                        self.api.CloseHandle(thread)
                    break
                present = self.api.Thread32Next(snapshot, c.byref(entry))
        finally:
            self.api.CloseHandle(snapshot)
        raise PilotError("Windows could not resume the owned child process.")

    def alive(self):
        info = self.Accounting()
        if not self.api.QueryInformationJobObject(self.handle, 1, self.ctypes.byref(info), self.ctypes.sizeof(info), None):
            raise PilotError("Windows could not verify owned process cleanup.")
        return bool(info.ActiveProcesses)

    def force(self):
        if not self.api.TerminateJobObject(self.handle, 1):
            raise PilotError("Windows could not stop the owned process tree.")

    def close(self):
        if self.handle:
            self.api.CloseHandle(self.handle)
            self.handle = None


@dataclass
class OwnedChild:
    process: subprocess.Popen
    label: str
    job: WindowsJob | None = None
    resumed: bool = True

    def alive(self):
        self.process.poll()  # Reap an exited POSIX leader before checking its group.
        if self.job is not None:
            return self.job.alive()
        try:
            os.killpg(self.process.pid, 0)
            return True
        except ProcessLookupError:
            return False

    def graceful(self):
        if not self.resumed:
            return
        try:
            if self.job is not None:
                os.kill(self.process.pid, signal.CTRL_BREAK_EVENT)
            else:
                os.killpg(self.process.pid, signal.SIGTERM)
        except (ProcessLookupError, PermissionError, OSError):
            # Missing Windows consoles cannot receive CTRL_BREAK. The bounded
            # job-object fallback still owns only our children.
            pass

    def force(self):
        if self.job is not None:
            self.job.force()
        else:
            try:
                os.killpg(self.process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass


class ProcessOwner:
    def __init__(self, stop):
        self.stop = stop
        self.children = []

    def start(self, argv, *, cwd, env, label):
        self.stop.check()
        job = WindowsJob() if WINDOWS else None
        options = {"creationflags": 0x200 | 0x4} if WINDOWS else {"start_new_session": True}
        try:
            process = subprocess.Popen(list(argv), cwd=cwd, env=env, shell=False,
                                       stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                       stderr=subprocess.DEVNULL, **options)
        except (OSError, ValueError):
            if job:
                job.close()
            raise PilotError(f"Could not start {label}. Check prerequisites and retry --setup.") from None
        child = OwnedChild(process, label, job, resumed=not WINDOWS)
        self.children.append(child)
        if job:
            try:
                job.assign_and_resume(process)
                child.resumed = True
            except Exception:
                # The initial process is still suspended if assignment failed;
                # it cannot have spawned children. Kill and reap this exact PID.
                if process.poll() is None:
                    process.kill()
                process.wait(timeout=FORCE_TIMEOUT)
                job.close()
                self.children.remove(child)
                raise
        return child

    def assert_running(self):
        self.stop.check()
        for child in self.children:
            status = child.process.poll()
            if status is not None:
                raise PilotError(f"{child.label} stopped unexpectedly (exit {status}). Both pilot servers will be stopped.")

    def run(self, argv, *, cwd, env, label, timeout=900):
        child = self.start(argv, cwd=cwd, env=env, label=label)
        deadline = time.monotonic() + timeout
        while child.process.poll() is None:
            self.stop.check()
            if time.monotonic() >= deadline:
                raise PilotError(f"{label} timed out. Setup is incomplete; retry --setup after fixing prerequisites.")
            time.sleep(POLL_INTERVAL)
        status = child.process.returncode
        self.stop_children([child])
        if status != 0:
            raise PilotError(f"{label} failed (exit {status}). Setup is incomplete; check connectivity and retry --setup.")

    def stop_children(self, children=None):
        targets = list(reversed(self.children if children is None else children))
        if not targets:
            return
        for child in targets:
            child.graceful()
        deadline = time.monotonic() + STOP_TIMEOUT
        pending = targets
        while pending and time.monotonic() < deadline:
            pending = [child for child in pending if child.alive()]
            if pending:
                time.sleep(POLL_INTERVAL)
        for child in pending:
            child.force()
        deadline = time.monotonic() + FORCE_TIMEOUT
        while pending and time.monotonic() < deadline:
            pending = [child for child in pending if child.alive()]
            if pending:
                time.sleep(POLL_INTERVAL)
        if pending:
            raise PilotError("Owned child cleanup could not be confirmed; temporary pilot data is retained.")
        for child in targets:
            child.process.wait(timeout=FORCE_TIMEOUT)
            if child.job:
                child.job.close()
            self.children.remove(child)


@contextmanager
def reserve_ports():
    """Hold exclusive listening reservations before runtime or installer work."""
    reservations = {}
    try:
        for port in (API_PORT, WEB_PORT):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            reservations[port] = sock
            if WINDOWS:
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            else:
                # Reuse TIME_WAIT connections, never an active listener.
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind((HOST, port))
                # SO_REUSEADDR permits two bound sockets until one listens.
                # Listen before yielding so another launcher cannot enter setup.
                sock.listen(1)
            except OSError:
                raise PilotError(f"Port {port} is already in use. Stop its owner yourself, then retry; no existing server will be reused or stopped.") from None
        yield reservations
    finally:
        for sock in reservations.values():
            sock.close()


def setup(root, node, env, owner):
    npm = resolve_npm_cli(node)
    managed_venv(root, create=True)
    prepared = root / ".venv" / PREPARED_MARKER
    if prepared.is_symlink():
        raise PilotError("Refusing a symlink at the pilot setup marker. Use a clean project directory.")
    prepared.unlink(missing_ok=True)  # Interrupted setup must not retain an old success marker.
    python = venv_python(root)
    # Put the verified Node first for the existing npm build scripts as well.
    env = {**env, "PATH": str(node.parent) + os.pathsep + env.get("PATH", "")}
    print("Setting up the original reader pilot from the existing dependency locks...", flush=True)
    # Re-run the non-destructive bootstrap only inside our verified owned venv.
    # An interrupted ensurepip can leave Python present but pip missing.
    owner.run([sys.executable, "-m", "venv", "--copies", str(root / ".venv")],
              cwd=root, env=env, label="project-local Python environment")
    check_venv_python(root, env)
    owner.run([str(python), "-m", "pip", "--isolated", "install", "--disable-pip-version-check",
               "--no-input", "--require-hashes", "--only-binary=:all:",
               "-r", str(root / "requirements-extras/pilot-api.txt"),
               "-r", str(root / "requirements-extras/symbolic.txt")],
              cwd=root, env=env, label="hash-pinned Python dependencies")
    owner.run([str(python), "-m", "pip", "--isolated", "check"], cwd=root, env=env,
              label="Python dependency verification")
    owner.run([str(node), str(npm), "ci", "--no-audit", "--no-fund"],
              cwd=root / "app/web", env=env, label="locked web dependencies")
    owner.run([str(node), str(npm), "run", "build"], cwd=root / "app/web", env=env,
              label="reader web build")
    check_venv_python(root, env, dependencies=True)
    save_prepared_setup(root)


def check_venv_python(root, env, *, dependencies=False):
    expected = pinned_python_versions(root) if dependencies else {}
    imports = "import fastapi,uvicorn,sympy; " if dependencies else ""
    probe = ("import json,platform,sys,importlib.metadata; " + imports +
             "names=" + repr(sorted(expected)) + "; " +
             "print(json.dumps([platform.python_implementation(),list(sys.version_info[:2]),sys.prefix,"
             "{name:importlib.metadata.version(name) for name in names}]))")
    output = command_output([str(venv_python(root)), "-c", probe], cwd=root, env=env)
    try:
        implementation, version, prefix, installed = json.loads(output)
        if (implementation != "CPython" or version != [3, 13] or
                Path(prefix).resolve() != (root / ".venv").resolve() or installed != expected):
            raise ValueError()
    except (ValueError, TypeError, OSError):
        raise PilotError("The project .venv must use CPython 3.13.x with the pinned pilot dependencies. Retry --setup in a clean project directory.") from None


def check_installation(root, env):
    managed_venv(root)
    for path in (venv_python(root), root / "app/web/node_modules/vite/bin/vite.js", root / "app/web/dist/index.html"):
        if not path.is_file():
            raise PilotError("The local pilot setup is missing or incomplete. Run python tools/run_reader_pilot.py --setup.")
    check_prepared_setup(root)
    check_venv_python(root, env, dependencies=True)


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def read_response(opener, url, timeout):
    with opener.open(url, timeout=timeout) as response:
        if response.status != 200:
            raise ValueError("not ready")
        body = response.read(MAX_RESPONSE + 1)
        if len(body) > MAX_RESPONSE:
            raise ValueError("response too large")
        return body


def original_ready(opener, base, timeout):
    library = json.loads(read_response(opener, base + "/api/library", timeout))
    if not isinstance(library, dict) or library.get("library_id") != LIBRARY_ID:
        return False
    courses = library.get("courses")
    if not isinstance(courses, list) or len(courses) != 1 or not isinstance(courses[0], dict):
        return False
    if courses[0].get("course_id") != COURSE_ID or courses[0].get("book_id") != BOOK_ID:
        return False
    detail = json.loads(read_response(opener, base + "/api/courses/" + COURSE_ID, timeout))
    course = detail.get("course") if isinstance(detail, dict) else None
    return isinstance(course, dict) and course.get("course_id") == COURSE_ID and course.get("book_id") == BOOK_ID


def wait_ready(owner, *, web=False, timeout=STARTUP_TIMEOUT):
    # Proxy settings and redirects must never turn a loopback check into an
    # external request. No response body is printed or persisted.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    deadline = time.monotonic() + timeout
    base = f"http://{HOST}:{WEB_PORT if web else API_PORT}"
    while time.monotonic() < deadline:
        owner.assert_running()
        try:
            remaining = max(0.01, min(1.0, deadline - time.monotonic()))
            ready = original_ready(opener, base, remaining)
            if ready and web:
                read_response(opener, base + "/", remaining)
            owner.assert_running()
            if ready:
                return
        except (OSError, urllib.error.URLError, ValueError):
            pass
        time.sleep(POLL_INTERVAL)
    raise PilotError(f"{'Reader page' if web else 'Original API'} did not become ready in time. Both pilot servers will be stopped.")


def launch(root, node, env, owner, reservations, *, check=False):
    # Explicit ownership retains uncertain-cleanup data without a finalizer.
    # mkdtemp also supports the Python 3.11 contract-test environment.
    temp_root = Path(tempfile.mkdtemp(prefix="book-reader-launcher-"))
    api_env = {**env, "TMP": str(temp_root), "TEMP": str(temp_root), "TMPDIR": str(temp_root),
               "BOOK_APP_DATA_DIR": str(temp_root / "app-data")}
    preview_env = {**api_env, "NODE_COMPILE_CACHE": str(temp_root / "node-compile-cache")}
    try:
        reservations[API_PORT].close()
        owner.start([str(venv_python(root)), "-m", "uvicorn", API_FACTORY, "--factory",
                     "--host", HOST, "--port", str(API_PORT), "--workers", "1", "--no-access-log"],
                    cwd=root, env=api_env, label="original fixture API")
        wait_ready(owner)
        reservations[WEB_PORT].close()
        owner.start([str(node), str(root / "app/web/node_modules/vite/bin/vite.js"), "preview",
                     "--host", HOST, "--port", str(WEB_PORT), "--strictPort"],
                    cwd=root / "app/web", env=preview_env, label="reader preview")
        wait_ready(owner, web=True)
        print(f"Original reader ready: http://{HOST}:{WEB_PORT}/", flush=True)
        if not check:
            print("Press Ctrl+C to stop both servers. Sample progress is temporary.", flush=True)
            while True:
                owner.assert_running()
                time.sleep(POLL_INTERVAL)
    finally:
        try:
            owner.stop_children()
        except Exception:
            print(f"Cleanup is incomplete; original sample data remains at {temp_root}", file=sys.stderr, flush=True)
            raise
        try:
            shutil.rmtree(temp_root)
        except OSError:
            raise PilotError(f"Servers stopped, but temporary sample data could not be removed: {temp_root}") from None
        if temp_root.exists():
            raise PilotError(f"Servers stopped, but temporary sample data remains: {temp_root}")
    if check:
        print("Original API, reader page and proxy checked; owned servers stopped and temporary data removed.", flush=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--setup", action="store_true", help="explicitly install locked dependencies and build, then launch")
    parser.add_argument("--check", action="store_true", help="start, verify original API/page/proxy, stop and exit")
    args = parser.parse_args(argv)
    stop = StopRequest()
    owner = ProcessOwner(stop)
    try:
        require_python()
        with handle_signals(stop):
            try:
                with reserve_ports() as reservations:
                    env = clean_environment()
                    node = resolve_node(ROOT, env)
                    if args.setup:
                        setup(ROOT, node, env, owner)
                    check_installation(ROOT, env)
                    stop.check()
                    launch(ROOT, node, env, owner, reservations, check=args.check)
            finally:
                # Also covers interrupted/failed setup. Keep interrupt handlers
                # installed until every owned process has actually stopped.
                owner.stop_children()
        return 0
    except (PilotInterrupted, KeyboardInterrupt):
        print("Original reader stopped.", flush=True)
        return 130
    except PilotError as exc:
        print(f"Reader pilot: {exc}", file=sys.stderr, flush=True)
        return 1
    except OSError:
        print("Reader pilot: a local file or process operation failed. Check permissions and prerequisites.", file=sys.stderr, flush=True)
        return 1
    except subprocess.TimeoutExpired:
        print("Reader pilot: owned process cleanup timed out. Cleanup is incomplete.", file=sys.stderr, flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
