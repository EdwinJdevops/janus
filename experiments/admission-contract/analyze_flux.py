"""Summarize attributed requests and convergence from retained Flux experiments."""
import argparse
import collections
import datetime
import json
import math
import pathlib
import statistics


def percentile(values, fraction):
    if not values:
        return None
    ordered = sorted(values)
    return ordered[math.ceil(len(ordered) * fraction) - 1]


def analyze(directory):
    def read(name):
        return json.loads((directory / name).read_text())
    timeline = [json.loads(line) for line in (directory / 'timeline.jsonl').read_text().splitlines()]
    events = {row['event']: row for row in timeline}
    resumes = [row['time'] for row in timeline if row['event'] == 'backend_resumed']
    fault_end = min(resumes) if resumes else events['fault_ended']['time']
    phases = {
        'healthy': (events['healthy_started']['time'], events['healthy_ended']['time']),
        'fault': (events['fault_started']['time'], fault_end),
        'recovery': (fault_end, events['recovered']['time']),
    }
    result = {'run': directory.name, 'treatment': read('treatment.json'),
              'cleanup': read('cleanup.json'), 'phases': {},
              'recovery_seconds': events['recovered']['time'] - fault_end,
              'reported_observer_recovery_seconds': events['recovered']['convergence_seconds']}
    if resumes:
        result['backend_pause_seconds'] = min(resumes) - events['fault_started']['time']
        result['backend_resume_events'] = len(resumes)
    audit = []
    for line in (directory / 'audit.jsonl').read_text().splitlines():
        row = json.loads(line)
        if row['stage'] != 'ResponseComplete' or row['verb'] == 'watch':
            continue
        if row['user']['username'] != 'system:serviceaccount:flux-system:controller':
            continue
        audit.append(row)
    admissions = [json.loads(line) for line in (directory / 'admissions.jsonl').read_text().splitlines()]
    for phase, (begin, end) in phases.items():
        codes = collections.Counter()
        verbs = collections.Counter()
        latencies = []
        overlapping_latencies = []
        overlapping_codes = collections.Counter()
        overlapping_request_seconds = 0
        workload_writes = 0
        for row in audit:
            started = datetime.datetime.fromisoformat(row['requestReceivedTimestamp'].replace('Z', '+00:00')).timestamp()
            finished = datetime.datetime.fromisoformat(row['stageTimestamp'].replace('Z', '+00:00')).timestamp()
            overlap = max(0, min(end, finished) - max(begin, started))
            if overlap:
                overlapping_latencies.append((finished - started) * 1000)
                overlapping_codes[str(row['responseStatus']['code'])] += 1
                overlapping_request_seconds += overlap
            if not begin <= started < end:
                continue
            latencies.append((finished - started) * 1000)
            codes[str(row['responseStatus']['code'])] += 1
            verbs[row['verb']] += 1
            reference = row.get('objectRef', {})
            if reference.get('resource') == 'configmaps' and reference.get('namespace') == 'janus-workload' and row['verb'] in ('create', 'patch', 'update', 'delete'):
                workload_writes += 1
        admitted = [row for row in admissions if begin <= row['time'] < end]
        result['phases'][phase] = {
            'duration_seconds': end - begin, 'requests': sum(codes.values()),
            'requests_per_second': sum(codes.values()) / (end - begin),
            'requests_overlapping_phase': len(overlapping_latencies),
            'overlapping_status_codes': dict(overlapping_codes),
            'overlapping_request_seconds': overlapping_request_seconds,
            'p99_total_latency_of_overlapping_requests_ms': percentile(overlapping_latencies, 0.99),
            'status_codes': dict(codes), 'verbs': dict(verbs),
            'workload_write_requests_including_dry_run': workload_writes,
            'median_request_latency_ms': statistics.median(latencies) if latencies else None,
            'p95_request_latency_ms': percentile(latencies, 0.95),
            'p99_request_latency_ms': percentile(latencies, 0.99),
            'admission_requests_received': len(admitted),
            'admission_decisions_deny': sum(not row['allowed'] for row in admitted),
        }
    if not result['cleanup']['processes_stopped']:
        raise RuntimeError((directory, 'cleanup incomplete'))
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('runs', type=pathlib.Path, nargs='+')
    parser.add_argument('--output', type=pathlib.Path, required=True)
    args = parser.parse_args()
    results = [analyze(directory) for directory in args.runs]
    args.output.write_text(json.dumps(results, indent=2))
    for result in results:
        fault = result['phases']['fault']
        print(result['run'], 'fault requests', fault['requests'], '429', fault['status_codes'].get('429', 0),
              'recovery seconds', round(result['recovery_seconds'], 2))


if __name__ == '__main__':
    main()
