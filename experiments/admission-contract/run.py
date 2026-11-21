import base64
import argparse
import hashlib
import http.server
import json
import pathlib
import secrets
import signal
import socket
import ssl
import subprocess
import tempfile
import threading
import time
import urllib.error
import urllib.request

parser = argparse.ArgumentParser(description='Disposable local Kubernetes admission contract experiment')
parser.add_argument('--assets', required=True, type=pathlib.Path)
parser.add_argument('--output', required=True, type=pathlib.Path)
args = parser.parse_args()
BIN = args.assets.resolve()
OUT = args.output.resolve()
# Refuse to mix evidence from separate runs.
OUT.mkdir(parents=True, exist_ok=False)

def port():
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]

def main():
    def interrupted(signum, frame):
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, interrupted)
    metadata = {'binaries': {}}
    for name in ['etcd', 'kube-apiserver']:
        binary = BIN / name
        with binary.open('rb') as stream:
            digest = hashlib.file_digest(stream, 'sha256').hexdigest()
        metadata['binaries'][name] = {
            'sha256': digest,
            'version': subprocess.check_output([str(binary), '--version'], text=True).strip(),
        }
    (OUT / 'metadata.json').write_text(json.dumps(metadata, indent=2))
    processes = []
    logs = []
    server = None
    results = []
    with tempfile.TemporaryDirectory(prefix='janus-') as tmp:
        tmp = pathlib.Path(tmp)
        def run(args):
            subprocess.run(args, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        key, cert = tmp / 'key.pem', tmp / 'cert.pem'
        run(['openssl', 'req', '-x509', '-newkey', 'rsa:2048', '-nodes', '-keyout', str(key), '-out', str(cert), '-days', '1', '-subj', '/CN=localhost', '-addext', 'subjectAltName=IP:127.0.0.1,DNS:localhost'])
        token = secrets.token_hex(32)
        tokens = tmp / 'tokens.csv'
        tokens.write_text(token + ',janus,janus,"system:masters"\n')
        tokens.chmod(0o600)
        ep, peer, ap = port(), port(), port()
        def start(name, args):
            log = open(OUT / (name + '.log'), 'w')
            logs.append(log)
            try:
                process = subprocess.Popen(args, stdout=log, stderr=log)
            except Exception:
                for previous in processes:
                    previous.terminate()
                    previous.wait(timeout=15)
                raise
            processes.append(process)
        start('etcd', [str(BIN / 'etcd'), '--data-dir', str(tmp / 'etcd'), '--listen-client-urls', f'http://127.0.0.1:{ep}', '--advertise-client-urls', f'http://127.0.0.1:{ep}', '--listen-peer-urls', f'http://127.0.0.1:{peer}', '--initial-advertise-peer-urls', f'http://127.0.0.1:{peer}', '--initial-cluster', f'default=http://127.0.0.1:{peer}'])
        start('apiserver', [str(BIN / 'kube-apiserver'), '--bind-address=127.0.0.1', '--advertise-address=127.0.0.1', f'--secure-port={ap}', f'--etcd-servers=http://127.0.0.1:{ep}', f'--cert-dir={tmp}', f'--tls-cert-file={cert}', f'--tls-private-key-file={key}', f'--token-auth-file={tokens}', '--authorization-mode=RBAC', '--service-cluster-ip-range=10.253.0.0/24', '--service-account-issuer=https://janus.local', f'--service-account-key-file={cert}', f'--service-account-signing-key-file={key}', '--disable-admission-plugins=ServiceAccount'])
        context = ssl.create_default_context(cafile=str(cert))
        def request(method, path, body=None):
            req = urllib.request.Request(f'https://127.0.0.1:{ap}' + path, data=json.dumps(body).encode() if body is not None else None, method=method, headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'})
            try:
                response = urllib.request.urlopen(req, context=context, timeout=10)
            except urllib.error.HTTPError as error:
                response = error
            return response.code, response.read().decode()
        try:
            for _ in range(90):
                try:
                    if request('GET', '/readyz')[0] == 200:
                        break
                except (OSError, urllib.error.URLError):
                    pass
                if any(p.poll() is not None for p in processes):
                    raise RuntimeError('control plane exited, inspect logs')
                time.sleep(1)
            else:
                raise RuntimeError('control plane readiness timeout')
            class Hook(http.server.BaseHTTPRequestHandler):
                def do_POST(self):
                    review = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
                    with open(OUT / 'reviews.jsonl', 'a') as f:
                        f.write(json.dumps(review) + '\n')
                    response = {'apiVersion': 'admission.k8s.io/v1', 'kind': 'AdmissionReview', 'response': {'uid': review['request']['uid'], 'allowed': False, 'status': {'code': 429, 'message': 'JANUS synthetic contract'}}}
                    data = json.dumps(response).encode()
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(data)
                def log_message(self, *args):
                    pass
            server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), Hook)
            tls = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            tls.load_cert_chain(cert, key)
            server.socket = tls.wrap_socket(server.socket, server_side=True)
            threading.Thread(target=server.serve_forever, daemon=True).start()
            hp = server.server_port
            for ns in ['janus-test', 'janus-control']:
                code, body = request('POST', '/api/v1/namespaces', {'apiVersion': 'v1', 'kind': 'Namespace', 'metadata': {'name': ns}})
                if code != 201:
                    raise RuntimeError((code, body))
            hookpath = '/apis/admissionregistration.k8s.io/v1/validatingwebhookconfigurations'
            def configure(policy, target):
                config = {'apiVersion': 'admissionregistration.k8s.io/v1', 'kind': 'ValidatingWebhookConfiguration', 'metadata': {'name': 'janus-contract'}, 'webhooks': [{'name': 'contract.janus.local', 'admissionReviewVersions': ['v1'], 'sideEffects': 'None', 'timeoutSeconds': 2, 'failurePolicy': policy, 'clientConfig': {'url': f'https://127.0.0.1:{target}/', 'caBundle': base64.b64encode(cert.read_bytes()).decode()}, 'namespaceSelector': {'matchLabels': {'kubernetes.io/metadata.name': 'janus-test'}}, 'rules': [{'operations': ['CREATE'], 'apiGroups': [''], 'apiVersions': ['v1'], 'resources': ['configmaps'], 'scope': 'Namespaced'}]}]}
                code, old = request('GET', hookpath + '/janus-contract')
                if code == 200:
                    config['metadata']['resourceVersion'] = json.loads(old)['metadata']['resourceVersion']
                    code, body = request('PUT', hookpath + '/janus-contract', config)
                else:
                    code, body = request('POST', hookpath, config)
                if code not in (200, 201):
                    raise RuntimeError((code, body))
                time.sleep(3)
            def probe(name, ns, expected):
                code, body = request('POST', f'/api/v1/namespaces/{ns}/configmaps', {'apiVersion': 'v1', 'kind': 'ConfigMap', 'metadata': {'name': name}})
                result = {'case': name, 'namespace': ns, 'expected': expected, 'http_status': code, 'body': json.loads(body), 'timestamp': time.time()}
                results.append(result)
                (OUT / 'results.json').write_text(json.dumps(results, indent=2))
                print(name, code, flush=True)
                if code != expected:
                    raise RuntimeError(result)
                stored, _ = request('GET', f'/api/v1/namespaces/{ns}/configmaps/{name}')
                expected_stored = 200 if expected == 201 else 404
                if stored != expected_stored:
                    raise RuntimeError((name, stored, expected_stored))
                result['stored_object_http_status'] = stored
                (OUT / 'results.json').write_text(json.dumps(results, indent=2))
            probe('baseline', 'janus-test', 201)
            for policy in ['Ignore', 'Fail']:
                configure(policy, hp)
                probe('deny-' + policy.lower(), 'janus-test', 429)
                probe('outside-' + policy.lower(), 'janus-control', 201)
            server.shutdown()
            server.server_close()
            server = None
            for policy, expected in [('Ignore', 201), ('Fail', 500)]:
                configure(policy, hp)
                probe('outage-' + policy.lower(), 'janus-test', expected)
            print('All admission contract cases passed', flush=True)
        finally:
            if server:
                server.shutdown()
                server.server_close()
            for process in reversed(processes):
                process.terminate()
                try:
                    process.wait(timeout=15)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
            for log in logs:
                log.close()
            (OUT / 'cleanup.json').write_text(json.dumps({'processes_stopped': all(p.poll() is not None for p in processes), 'pids': [p.pid for p in processes]}))

if __name__ == '__main__':
    main()
