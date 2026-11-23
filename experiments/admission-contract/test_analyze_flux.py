import json
import pathlib
import tempfile
import unittest

from analyze_flux import analyze, percentile


class AuditPhaseTests(unittest.TestCase):
    def test_request_started_before_pause_still_counts_as_in_flight(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = pathlib.Path(temporary)
            (directory / 'treatment.json').write_text(json.dumps({'treatment': 'default'}))
            (directory / 'cleanup.json').write_text(json.dumps({'processes_stopped': True}))
            timeline = [
                {'event': 'healthy_started', 'time': 0},
                {'event': 'healthy_ended', 'time': 5},
                {'event': 'fault_started', 'time': 5},
                {'event': 'fault_ended', 'time': 10},
                {'event': 'recovered', 'time': 15, 'convergence_seconds': 5},
            ]
            (directory / 'timeline.jsonl').write_text('\n'.join(json.dumps(row) for row in timeline))
            request = {
                'stage': 'ResponseComplete', 'verb': 'patch',
                'user': {'username': 'system:serviceaccount:flux-system:controller'},
                'requestReceivedTimestamp': '1970-01-01T00:00:04Z',
                'stageTimestamp': '1970-01-01T00:00:12Z',
                'responseStatus': {'code': 200},
                'objectRef': {'resource': 'configmaps', 'namespace': 'janus-workload'},
            }
            administrator = dict(request, user={'username': 'janus'})
            watch = dict(request, verb='watch')
            (directory / 'audit.jsonl').write_text('\n'.join(json.dumps(row) for row in [request, administrator, watch]))
            (directory / 'admissions.jsonl').write_text('')
            result = analyze(directory)
            fault = result['phases']['fault']
            self.assertEqual(fault['requests'], 0)
            self.assertEqual(fault['requests_overlapping_phase'], 1)
            self.assertEqual(fault['overlapping_request_seconds'], 5)
            self.assertEqual(fault['p99_total_latency_of_overlapping_requests_ms'], 8000)
            self.assertEqual(result['phases']['recovery']['overlapping_request_seconds'], 2)

    def test_nearest_rank_percentiles(self):
        self.assertEqual(percentile(list(range(1, 101)), 0.95), 95)
        self.assertEqual(percentile([7], 0.99), 7)
        self.assertIsNone(percentile([], 0.99))


if __name__ == '__main__':
    unittest.main()
