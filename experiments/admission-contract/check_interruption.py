"""Verify teardown after terminating the runner while its backend is paused."""
import argparse
import json
import os
import pathlib
import signal
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--assets', required=True)
    parser.add_argument('--flux-assets', required=True)
    parser.add_argument('--output', required=True, type=pathlib.Path)
    args = parser.parse_args()
    runner = pathlib.Path(__file__).with_name('run.py')
    process = subprocess.Popen([
        sys.executable, str(runner), '--assets', args.assets,
        '--flux-assets', args.flux_assets, '--fault-mode', 'etcd-pause',
        '--output', str(args.output),
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True)
    interrupted = False
    try:
        for line in process.stdout:
            if line.startswith('fault_started'):
                process.send_signal(signal.SIGTERM)
                interrupted = True
                break
        _, errors = process.communicate(timeout=45)
    finally:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGCONT)
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=20)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
    if not interrupted:
        raise RuntimeError('Runner ended before the interruption target: ' + errors[-2000:])
    cleanup = json.loads((args.output / 'cleanup.json').read_text())
    timeline = [json.loads(line) for line in (args.output / 'timeline.jsonl').read_text().splitlines()]
    resumes = sum(row['event'] == 'backend_resumed' for row in timeline)
    if process.returncode == 0 or not cleanup['processes_stopped'] or resumes != 1:
        raise RuntimeError((process.returncode, cleanup, resumes))
    (args.output / 'interruption-check.json').write_text(json.dumps({
        'interrupted_during_backend_pause': True,
        'backend_resume_events': resumes,
        'processes_stopped': cleanup['processes_stopped'],
        'runner_exit_code': process.returncode,
    }, indent=2))
    print('Interruption check passed: backend resumed once and children stopped')


if __name__ == '__main__':
    main()
