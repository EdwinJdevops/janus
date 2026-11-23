"""Bounded Flux retry comparison using an independent artifact and admission fixture."""
import base64
import collections
import hashlib
import gzip
import http.server
import io
import json
import os
import pathlib
import signal
import ssl
import subprocess
import tarfile
import threading
import time
import urllib.request

SCENARIO_SHA256 = hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest()

def experiment(request, start, port, tmp, output, binaries, assets, treatment,
               api_port, etcd_port, cert, key, controller_token, fault_mode, backend_process):
    count = 8
    state = {'fault': False}
    artifacts = {}
    servers = []
    events = []
    event_lock = threading.Lock()
    admission_events = []
    transport_events = []
    readiness_seen = collections.defaultdict(set)
    resume_timer = None
    backend_paused = False
    resume_lock = threading.Lock()
    backend_resume_wall = None
    backend_resume_clock = None
    def record(event, at=None, **values):
        row = {'event': event, 'time': time.time() if at is None else at, **values}
        with event_lock:
            events.append(row)
            with (output / 'timeline.jsonl').open('a') as stream:
                stream.write(json.dumps(row) + '\n')
        print(event, values, flush=True)

    def checked(method, path, body=None, expected=(200, 201)):
        code, text = request(method, path, body)
        if code not in expected:
            raise RuntimeError((method, path, code, text))
        return json.loads(text)

    kubeconfig = tmp / 'controller-kubeconfig.json'
    kubeconfig.write_text(json.dumps({
        'apiVersion': 'v1', 'kind': 'Config', 'current-context': 'janus',
        'clusters': [{'name': 'janus', 'cluster': {
            'server': f'https://127.0.0.1:{api_port}',
            'certificate-authority-data': base64.b64encode(cert.read_bytes()).decode()}}],
        'users': [{'name': 'controller', 'user': {'token': controller_token}}],
        'contexts': [{'name': 'janus', 'context': {'cluster': 'janus', 'user': 'controller'}}],
    }))
    kubeconfig.chmod(0o600)
    # CRDs are public inputs. Administrative commands use a separate ephemeral
    # kubeconfig supplied by the parent, never the user's current context.
    admin_config = tmp / 'admin-kubeconfig.json'
    admin_data = json.loads(kubeconfig.read_text())
    admin_data['users'][0]['user']['token'] = (tmp / 'tokens.csv').read_text().split(',')[0]
    admin_config.write_text(json.dumps(admin_data))
    admin_config.chmod(0o600)
    kubectl = [str(binaries / 'kubectl'), '--kubeconfig', str(admin_config), '--request-timeout=20s']
    for crd in sorted(assets.glob('*.yaml')):
        completed = subprocess.run(kubectl + ['apply', '-f', str(crd)], capture_output=True, text=True, timeout=60)
        if completed.returncode:
            raise RuntimeError(('CRD installation', crd.name, completed.stderr))
    subprocess.run(kubectl + ['wait', '--for=condition=Established', 'crd', '--all', '--timeout=60s'], check=True, capture_output=True, timeout=70)
    for namespace in ['flux-system', 'janus-workload']:
        checked('POST', '/api/v1/namespaces', {'apiVersion': 'v1', 'kind': 'Namespace', 'metadata': {'name': namespace}})
    checked('POST', '/apis/rbac.authorization.k8s.io/v1/clusterrolebindings', {
        'apiVersion': 'rbac.authorization.k8s.io/v1', 'kind': 'ClusterRoleBinding',
        'metadata': {'name': 'janus-controller'},
        'roleRef': {'apiGroup': 'rbac.authorization.k8s.io', 'kind': 'ClusterRole', 'name': 'cluster-admin'},
        'subjects': [{'kind': 'ServiceAccount', 'name': 'controller', 'namespace': 'flux-system'}],
    })
    if treatment == 'tuned':
        checked('POST', '/apis/flowcontrol.apiserver.k8s.io/v1/prioritylevelconfigurations', {
            'apiVersion': 'flowcontrol.apiserver.k8s.io/v1', 'kind': 'PriorityLevelConfiguration',
            'metadata': {'name': 'janus-controller'}, 'spec': {'type': 'Limited', 'limited': {
                'nominalConcurrencyShares': 5, 'lendablePercent': 0,
                'limitResponse': {'type': 'Queue', 'queuing': {'queues': 16, 'handSize': 4, 'queueLengthLimit': 16}}}}})
        checked('POST', '/apis/flowcontrol.apiserver.k8s.io/v1/flowschemas', {
            'apiVersion': 'flowcontrol.apiserver.k8s.io/v1', 'kind': 'FlowSchema',
            'metadata': {'name': 'janus-controller'}, 'spec': {
                'matchingPrecedence': 500, 'priorityLevelConfiguration': {'name': 'janus-controller'},
                'distinguisherMethod': {'type': 'ByUser'}, 'rules': [{
                    'subjects': [{'kind': 'ServiceAccount', 'serviceAccount': {'name': 'controller', 'namespace': 'flux-system'}}],
                    'resourceRules': [{'verbs': ['*'], 'apiGroups': ['*'], 'resources': ['*'], 'namespaces': ['*'], 'clusterScope': True}],
                    'nonResourceRules': [{'verbs': ['*'], 'nonResourceURLs': ['*']}]}]}})

    class Artifact(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            body = artifacts.get(self.path)
            if body is None:
                self.send_error(404)
                return
            self.send_response(200)
            self.end_headers()
            self.wfile.write(body)
        def log_message(self, *args):
            pass

    class Admission(http.server.BaseHTTPRequestHandler):
        def do_POST(self):
            review = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
            allowed = not state['fault']
            admission_events.append({'time': time.time(), 'allowed': allowed,
                'operation': review['request']['operation'],
                'dryRun': review['request'].get('dryRun', False),
                'name': review['request']['name'],
                'user': review['request']['userInfo']['username']})
            response = {'uid': review['request']['uid'], 'allowed': allowed}
            if not allowed:
                response['status'] = {'code': 429, 'message': 'bounded JANUS retry experiment'}
            data = json.dumps({'apiVersion': 'admission.k8s.io/v1', 'kind': 'AdmissionReview', 'response': response}).encode()
            try:
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(data)
            except (BrokenPipeError, ConnectionResetError):
                transport_events.append({'time': time.time(), 'event': 'client_disconnected',
                    'uid': review['request']['uid']})
        def log_message(self, *args):
            pass

    class FixtureServer(http.server.ThreadingHTTPServer):
        request_queue_size = 128
        daemon_threads = False
        def finish_request(self, connection, address):
            connection.settimeout(10)
            if hasattr(self, 'tls_context'):
                with self.tls_context.wrap_socket(connection, server_side=True) as wrapped:
                    self.RequestHandlerClass(wrapped, address, self)
            else:
                self.RequestHandlerClass(connection, address, self)

    def serve(handler, tls=False):
        server = FixtureServer(('127.0.0.1', 0), handler)
        if tls:
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.load_cert_chain(cert, key)
            server.tls_context = context
        servers.append(server)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        return server.server_port

    def make_artifact(revision):
        data = io.BytesIO()
        with tarfile.open(fileobj=data, mode='w') as archive:
            for app in range(count):
                resources = []
                for item in range(4):
                    name = f'cm-{item}.json'
                    resources.append(name)
                    body = json.dumps({'apiVersion': 'v1', 'kind': 'ConfigMap', 'metadata': {
                        'name': f'app-{app}-cm-{item}', 'namespace': 'janus-workload'},
                        'data': {'revision': str(revision)}}).encode()
                    info = tarfile.TarInfo(f'app-{app}/{name}')
                    info.size = len(body)
                    archive.addfile(info, io.BytesIO(body))
                body = json.dumps({'apiVersion': 'kustomize.config.k8s.io/v1beta1', 'kind': 'Kustomization', 'resources': resources}).encode()
                info = tarfile.TarInfo(f'app-{app}/kustomization.yaml')
                info.size = len(body)
                archive.addfile(info, io.BytesIO(body))
        body = gzip.compress(data.getvalue(), mtime=0)
        artifacts[f'/{revision}.tar.gz'] = body
        (output / f'artifact-{revision}.tar.gz').write_bytes(body)
        return hashlib.sha256(body).hexdigest()

    source_path = '/apis/source.toolkit.fluxcd.io/v1/namespaces/flux-system/gitrepositories'
    ks_path = '/apis/kustomize.toolkit.fluxcd.io/v1/namespaces/flux-system/kustomizations'
    def revision(number, artifact_port):
        digest = make_artifact(number)
        source = checked('GET', source_path + '/fixture')
        source['status'] = {'observedGeneration': 1, 'artifact': {
            'path': f'fixture/{number}.tar.gz', 'url': f'http://127.0.0.1:{artifact_port}/{number}.tar.gz',
            'revision': f'main@sha1:{number:040x}', 'digest': 'sha256:' + digest,
            'lastUpdateTime': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())},
            'conditions': [{'type': 'Ready', 'status': 'True', 'reason': 'Succeeded',
                'message': 'Local fixture artifact', 'lastTransitionTime': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}]}
        checked('PUT', source_path + '/fixture/status', source)

    def snapshot(name):
        code, metrics = request('GET', '/metrics')
        if code != 200:
            raise RuntimeError(('metrics', code))
        (output / f'{name}-apiserver.prom').write_text(metrics)
        with urllib.request.urlopen(f'http://127.0.0.1:{etcd_port}/metrics', timeout=5) as response:
            (output / f'{name}-etcd.prom').write_bytes(response.read())
        with urllib.request.urlopen(f'http://127.0.0.1:{metrics_port}/metrics', timeout=5) as response:
            (output / f'{name}-controller.prom').write_bytes(response.read())
        (output / f'{name}-kustomizations.json').write_text(json.dumps(checked('GET', ks_path), indent=2))
        (output / f'{name}-configmaps.json').write_text(json.dumps(checked('GET', '/api/v1/namespaces/janus-workload/configmaps'), indent=2))

    def converged(number):
        objects = checked('GET', '/api/v1/namespaces/janus-workload/configmaps')['items']
        if len(objects) != count * 4 or any(item.get('data', {}).get('revision') != str(number) for item in objects):
            return False
        items = checked('GET', ks_path)['items']
        target = f'main@sha1:{number:040x}'
        for item in items:
            status = item.get('status', {})
            if status.get('lastAppliedRevision') == target and any(
                condition['type'] == 'Ready' and condition['status'] == 'True'
                for condition in status.get('conditions', [])):
                readiness_seen[number].add(item['metadata']['name'])
        names = {item['metadata']['name'] for item in items}
        return len(items) == count and names <= readiness_seen[number] and all(
            item.get('status', {}).get('lastAppliedRevision') == target for item in items)

    def wait_convergence(number, timeout):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if converged(number):
                return
            time.sleep(1)
        raise RuntimeError(f'revision {number} failed to converge within {timeout}s')

    def resume_backend():
        nonlocal backend_paused, backend_resume_wall, backend_resume_clock
        with resume_lock:
            if backend_paused:
                backend_process.send_signal(signal.SIGCONT)
                backend_resume_wall = time.time()
                backend_resume_clock = time.monotonic()
                backend_paused = False
                record('backend_resumed', at=backend_resume_wall)

    try:
        artifact_port = serve(Artifact)
        admission_port = serve(Admission, tls=True)
        checked('POST', '/apis/admissionregistration.k8s.io/v1/validatingwebhookconfigurations', {
            'apiVersion': 'admissionregistration.k8s.io/v1', 'kind': 'ValidatingWebhookConfiguration',
            'metadata': {'name': 'janus-workload'}, 'webhooks': [{
                'name': 'retry.janus.local', 'admissionReviewVersions': ['v1'], 'sideEffects': 'None',
                'failurePolicy': 'Fail', 'timeoutSeconds': 2,
                'clientConfig': {'url': f'https://127.0.0.1:{admission_port}/', 'caBundle': base64.b64encode(cert.read_bytes()).decode()},
                'namespaceSelector': {'matchLabels': {'kubernetes.io/metadata.name': 'janus-workload'}},
                'rules': [{'operations': ['CREATE', 'UPDATE'], 'apiGroups': [''], 'apiVersions': ['v1'], 'resources': ['configmaps'], 'scope': 'Namespaced'}]}]})
        checked('POST', source_path, {'apiVersion': 'source.toolkit.fluxcd.io/v1', 'kind': 'GitRepository',
            'metadata': {'name': 'fixture', 'namespace': 'flux-system'}, 'spec': {'interval': '1m', 'url': 'https://example.invalid/fixture'}})
        revision(1, artifact_port)
        for app in range(count):
            spec = {'interval': '10s', 'path': f'./app-{app}', 'prune': False, 'timeout': '15s',
                'sourceRef': {'kind': 'GitRepository', 'name': 'fixture'}}
            if treatment == 'tuned':
                spec['retryInterval'] = '30s'
            checked('POST', ks_path, {'apiVersion': 'kustomize.toolkit.fluxcd.io/v1', 'kind': 'Kustomization',
                'metadata': {'name': f'app-{app}', 'namespace': 'flux-system'}, 'spec': spec})
        controller = assets / 'kustomize-controller'
        with controller.open('rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        crd_hashes = {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in assets.glob('*.yaml')}
        (output / 'treatment.json').write_text(json.dumps({'treatment': treatment, 'apps': count,
            'objects': count * 4, 'interval': '10s', 'retryInterval': '30s' if treatment == 'tuned' else '10s (inherits interval)',
            'concurrent': 1 if treatment == 'tuned' else 4,
            'fault_seconds': 35 if fault_mode == 'admission' else 10,
            'fault_mode': fault_mode, 'controller_sha256': digest,
            'scenario_sha256': SCENARIO_SHA256,
            'crd_sha256': crd_hashes, 'controller_image': 'ghcr.io/fluxcd/kustomize-controller@sha256:37db29b25dae35b881a5e064acedb0cc954442da453a39eaa0eab7a90dbecc4e'}, indent=2))
        (output / 'environment.json').write_text(json.dumps({'kernel': list(os.uname()),
            'meminfo': pathlib.Path('/proc/meminfo').read_text()}, indent=2))
        metrics_port = port()
        environment = dict(os.environ, KUBECONFIG=str(kubeconfig), RUNTIME_NAMESPACE='flux-system')
        start('flux', [str(controller),
            '--metrics-addr=127.0.0.1:' + str(metrics_port), '--health-addr=127.0.0.1:' + str(port()),
            '--concurrent=' + ('1' if treatment == 'tuned' else '4'), '--log-level=info'], env=environment)
        record('controller_started', treatment=treatment)
        wait_convergence(1, 120)
        record('baseline_converged')
        snapshot('healthy')
        record('healthy_started')
        healthy_deadline = time.monotonic() + 35
        revision(2, artifact_port)
        wait_convergence(2, 35)
        time.sleep(max(0, healthy_deadline - time.monotonic()))
        if not converged(2):
            snapshot('healthy-failed')
            raise RuntimeError('healthy revision did not converge during observation window')
        record('healthy_ended')
        snapshot('healthy-end')
        if fault_mode == 'admission':
            state['fault'] = True
            fault_deadline = time.monotonic() + 35
            record('fault_started', mode=fault_mode)
            revision(3, artifact_port)
        else:
            revision(3, artifact_port)
            record('source_revision_published')
            if backend_process.poll() is not None:
                raise RuntimeError('etcd exited before pause injection')
            backend_paused = True
            resume_timer = threading.Timer(10, resume_backend)
            resume_timer.start()
            backend_process.send_signal(signal.SIGSTOP)
            fault_deadline = time.monotonic() + 10
            record('fault_started', mode=fault_mode)
        time.sleep(max(0, fault_deadline - time.monotonic()))
        state['fault'] = False
        resume_backend()
        recovery = backend_resume_clock if fault_mode == 'etcd-pause' else time.monotonic()
        record('fault_ended', at=backend_resume_wall if fault_mode == 'etcd-pause' else None)
        snapshot('recovery-start')
        wait_convergence(3, 120)
        record('recovered', convergence_seconds=time.monotonic() - recovery)
        snapshot('recovered')
    finally:
        state['fault'] = False
        resume_backend()
        if resume_timer:
            resume_timer.cancel()
            resume_timer.join()
        for server in servers:
            server.shutdown()
            server.server_close()
        (output / 'admissions.jsonl').write_text(''.join(json.dumps(row) + '\n' for row in admission_events))
        (output / 'transport.jsonl').write_text(''.join(json.dumps(row) + '\n' for row in transport_events))
        record('fixture_stopped')
