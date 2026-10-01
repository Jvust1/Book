"""Hosted-only real launcher/page/owned-cleanup acceptance, with original fixtures."""
from __future__ import annotations

import json
import os
from pathlib import Path
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
PORTS = (8000, 5173)
COURSE = 'original_algebra_pilot'
LAUNCHER = ROOT / 'tools/run_reader_pilot.py'
HTTP = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def read(url: str) -> bytes:
    with HTTP.open(url, timeout=1) as response:
        require(response.status == 200, 'Unexpected local status')
        body = response.read(65537)
        require(len(body) <= 65536, 'Unexpected local response size')
        return body


def ready() -> bool:
    try:
        for origin in ('http://127.0.0.1:8000', 'http://127.0.0.1:5173'):
            payload = json.loads(read(origin + '/api/library'))
            require(payload['library_id'] == 'original_pilot_library', 'Non-original library identity')
            require([c['course_id'] for c in payload['courses']] == [COURSE], 'Non-original course identity')
        require(b'id="root"' in read('http://127.0.0.1:5173/'), 'Missing built page root')
        return True
    except (OSError, ValueError, KeyError, RuntimeError):
        return False


def assert_ports_free() -> None:
    for port in PORTS:
        with socket.socket() as listener:
            listener.bind(('127.0.0.1', port))


def stop(process: subprocess.Popen) -> None:
    if process.poll() is None:
        process.send_signal(signal.CTRL_BREAK_EVENT if os.name == 'nt' else signal.SIGINT)
    try:
        process.wait(timeout=25)
    except subprocess.TimeoutExpired:
        # Do not turn a stuck teardown into a false pass or kill by image name.
        if os.name == 'nt' and process.poll() is None:
            subprocess.run(['taskkill.exe', '/PID', str(process.pid), '/T', '/F'],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10, check=False)
        raise RuntimeError('Owned launcher did not stop within its cleanup budget') from None


def run_checked(args: list[str], *, env: dict[str, str], cwd: Path, timeout: int = 90) -> None:
    result = subprocess.run(args, cwd=cwd, env=env, shell=False, timeout=timeout,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    require(result.returncode == 0, 'Launcher command failed')


def main() -> int:
    if os.environ.get('BOOK_RUN_LAUNCHER_ACCEPTANCE') != '1':
        raise RuntimeError('Set BOOK_RUN_LAUNCHER_ACCEPTANCE=1 only in the dedicated hosted acceptance job')
    require(sys.version_info[:2] == (3, 13), 'Hosted launcher acceptance requires Python 3.13')
    node = shutil.which('node')
    require(node is not None, 'Node is required')
    assert_ports_free()
    with tempfile.TemporaryDirectory(prefix='book launcher acceptance ', delete=False) as workspace:
        root = Path(workspace)
        temporary = root / 'owned temporary data'
        unrelated = root / 'unrelated data'
        temporary.mkdir()
        unrelated.mkdir()
        sentinel = unrelated / 'sentinel.txt'
        sentinel.write_text('Original preservation sentinel', encoding='utf-8')
        env = dict(os.environ, TMP=str(temporary), TEMP=str(temporary), TMPDIR=str(temporary),
                   BOOK_APP_DATA_DIR=str(unrelated), PYTHONPATH='', PYTHONUTF8='1', PYTHONIOENCODING='utf-8')
        executable_dir = ROOT / '.venv' / ('Scripts' if os.name == 'nt' else 'bin')
        env['PATH'] = str(executable_dir) + os.pathsep + env.get('PATH', '')
        argv = [sys.executable, str(LAUNCHER)]
        flags = {'creationflags': subprocess.CREATE_NEW_PROCESS_GROUP} if os.name == 'nt' else {'start_new_session': True}
        with (root / 'launcher-output.txt').open('w', encoding='utf-8') as output:
            process = subprocess.Popen(argv, cwd=root, env=env, shell=False, stdout=output, stderr=output, **flags)
            failure: BaseException | None = None
            try:
                deadline = time.monotonic() + 60
                while not ready():
                    require(process.poll() is None, 'Launcher exited before original page readiness')
                    require(time.monotonic() < deadline, 'Launcher readiness budget exceeded')
                    time.sleep(0.2)
                require(process.poll() is None, 'Launcher must remain alive after startup')
                duplicate = subprocess.run(argv + ['--check'], cwd=root, env=env, shell=False,
                                           timeout=30, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                require(duplicate.returncode != 0, 'A second launcher adopted occupied ports')
                require(process.poll() is None and ready(), 'Second launch disturbed the first owner')
                # Dependency construction exercises the review repository without invoking an optional engine.
                request = urllib.request.Request(
                    f'http://127.0.0.1:8000/api/courses/{COURSE}/sections/original_s01/review-schedule',
                    data=b'{}', headers={'Content-Type': 'application/json'}, method='POST')
                try:
                    HTTP.open(request, timeout=3).close()
                except urllib.error.HTTPError as error:
                    require(error.code == 400, 'Unexpected original review validation status')
                else:
                    raise RuntimeError('Invalid review payload was accepted')
                require(sorted(p.name for p in unrelated.iterdir()) == ['sentinel.txt'], 'Fixture touched unrelated user data')
                # Existing original real browser journeys, using this launcher's API and preview.
                result = subprocess.run([str(node), str(ROOT / 'app/web/node_modules/@playwright/test/cli.js'),
                                         'test', '--config', 'playwright.pilot.config.ts'],
                                        cwd=ROOT / 'app/web', env=env, shell=False, timeout=480)
                require(result.returncode == 0, 'Launched original browser journeys failed')
            except BaseException as error:
                failure = error
                raise
            finally:
                try:
                    stop(process)
                except BaseException:
                    if failure is None:
                        raise
            require(process.returncode == 130, 'Launcher did not report its handled user interruption')
        assert_ports_free()
        require(not list(temporary.iterdir()), 'Owned temporary source/SQLite data remains after graceful stop')
        require(sentinel.read_text(encoding='utf-8') == 'Original preservation sentinel', 'Unrelated sentinel changed')
        run_checked(argv + ['--check'], env=env, cwd=root)
        assert_ports_free()
        require(not list(temporary.iterdir()), 'Immediate restart left temporary data')
        for port in PORTS:
            with socket.socket() as listener:
                listener.bind(('127.0.0.1', port))
                listener.listen()
                result = subprocess.run(argv + ['--check'], cwd=root, env=env, shell=False,
                                        timeout=30, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                require(result.returncode != 0, 'Launcher accepted an unrelated occupied port')
                require(listener.getsockname()[1] == port, 'Unrelated listener was closed')
                with socket.socket() as free:
                    free.bind(('127.0.0.1', next(p for p in PORTS if p != port)))
        assert_ports_free()
        require(not list(temporary.iterdir()), 'Rejected startup left temporary data')
    # Delete only this verifier's own workspace after all owned-process checks passed.
    shutil.rmtree(root)
    print('PASS: original page, browser journeys, occupied-port refusal, owned signal cleanup and restart')
    print('Signal exercised: Windows CTRL_BREAK_EVENT' if os.name == 'nt' else 'Signal exercised: POSIX SIGINT')
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError):
        print('FAIL: hosted launcher acceptance did not complete; no success is claimed', file=sys.stderr)
        raise SystemExit(1)
