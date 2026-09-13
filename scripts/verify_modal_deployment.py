"""Verifica el commit servido, BETO listo y una inferencia sin escribir en la BD."""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import time
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'apps/ml'))
from app.ml.model_release import identity, read_release


class VerificationError(Exception):
    pass


def verify(client, expected_sha: str, *, expected_model=None, attempts=6, retry_delay=10) -> dict:
    report = {'expected_sha': expected_sha, 'passed': False, 'attempts': []}
    for index in range(attempts):
        phase = 'health'
        started = time.monotonic()
        try:
            response = client.get('/health')
            response.raise_for_status()
            health = response.json()
            if health.get('deployment_sha') != expected_sha:
                raise VerificationError('health_sha_mismatch')
            beto = health.get('components', {}).get('beto', {})
            if health.get('status') != 'ok' or beto.get('ready') is not True or beto.get('status') != 'ready':
                raise VerificationError('beto_not_ready')
            if expected_model is not None and beto.get('model') != identity(expected_model):
                raise VerificationError('health_model_mismatch')
            phase = 'infer'
            response = client.post('/infer', json={'texts': [
                'La Constitución establece la organización de los poderes y las instituciones de la república.'
            ]})
            response.raise_for_status()
            body = response.json()
            if body.get('deployment_sha') != expected_sha:
                raise VerificationError('inference_sha_mismatch')
            if expected_model is not None and body.get('model') != identity(expected_model):
                raise VerificationError('inference_model_mismatch')
            predictions = body.get('predictions')
            if not isinstance(predictions, list) or len(predictions) != 1 or not isinstance(predictions[0], dict):
                raise VerificationError('invalid_prediction_count')
            prediction = predictions[0]
            label, confidence = prediction.get('label'), prediction.get('confidence')
            if (not isinstance(label, str) or not label.strip() or isinstance(confidence, bool)
                    or not isinstance(confidence, (int, float)) or not math.isfinite(confidence)
                    or not 0 <= confidence <= 1):
                raise VerificationError('invalid_prediction')
            if expected_model is not None and label not in expected_model['labels']:
                raise VerificationError('unknown_prediction_label')
            report.update(passed=True, served_sha=expected_sha, beto_ready=True)
            if expected_model is not None:
                report['served_model'] = identity(expected_model)
            report['attempts'].append({'number': index + 1, 'passed': True})
            return report
        except Exception as error:
            item = {'number': index + 1, 'passed': False, 'error_type': type(error).__name__,
                    'phase': phase, 'elapsed_seconds': round(time.monotonic() - started, 3)}
            if isinstance(error, VerificationError):
                item['reason'] = str(error)
            if isinstance(error, httpx.HTTPStatusError):
                item['http_status'] = error.response.status_code
            report['attempts'].append(item)
            # Un token incorrecto no se arregla esperando un arranque en frío.
            if isinstance(error, httpx.HTTPStatusError) and error.response.status_code in (401, 403):
                break
            if index + 1 < attempts:
                time.sleep(retry_delay)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', required=True)
    parser.add_argument('--expected-sha', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--model-manifest', type=Path, required=True)
    args = parser.parse_args()
    report = {'expected_sha': args.expected_sha, 'passed': False}
    try:
        if not re.fullmatch(r'[0-9a-f]{40}', args.expected_sha):
            raise ValueError('Expected a full commit SHA')
        headers = {header: os.environ[key] for header, key in (
            ('Modal-Key', 'MODAL_PROXY_TOKEN_ID'), ('Modal-Secret', 'MODAL_PROXY_TOKEN_SECRET'),
            ('X-Internal-Token', 'ML_INTERNAL_TOKEN'))}
        # No seguir redirecciones con credenciales del servicio.
        with httpx.Client(base_url=args.url.rstrip('/'), headers=headers, timeout=60, follow_redirects=False) as client:
            report = verify(client, args.expected_sha, expected_model=read_release(args.model_manifest))
    except Exception as error:
        report['error_type'] = type(error).__name__
    report['checked_at'] = datetime.now(timezone.utc).isoformat()
    report['scope'] = 'Deployment identity and inference contract; not semantic accuracy'
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report['passed'] else 1)


if __name__ == '__main__':
    main()
