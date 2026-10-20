"""Local hand recognition that triggers an OBS overlay for Teams' webcam."""

import argparse
import base64
import hashlib
import io
import json
import logging
import os
from pathlib import Path
import signal
import socket
import subprocess
import time
import uuid

import websocket

from gestures import ReactionTrigger, classify, reaction_anchor
from reactions import ANCHOR_REFERENCE, ASSET_DIR, DEFAULT_ANCHOR, REACTIONS
from settings import load_settings, update_settings


BASE = Path(__file__).resolve().parent
CONFIG = Path.home() / '.config/teams-effects'
SCENE = 'Teams Effects'
CAMERA = 'Webcam voor Teams'
PORT = 4467
LOG = logging.getLogger('teams-effects')


class ObsRequestError(RuntimeError):
    def __init__(self, kind, status):
        self.code = status['code']
        super().__init__(f'{kind}: {status}')


class Obs:
    def __init__(self):
        self.ws = websocket.create_connection(
            f'ws://127.0.0.1:{PORT}', timeout=5, http_no_proxy=['127.0.0.1'])
        try:
            hello = json.loads(self.ws.recv())
            identity = {'rpcVersion': 1, 'eventSubscriptions': 0}
            auth = hello['d'].get('authentication')
            if auth:
                password = (CONFIG / 'obs-password').read_text().strip()
                secret = base64.b64encode(hashlib.sha256(
                    (password + auth['salt']).encode()).digest()).decode()
                identity['authentication'] = base64.b64encode(hashlib.sha256(
                    (secret + auth['challenge']).encode()).digest()).decode()
            self.ws.send(json.dumps({'op': 1, 'd': identity}))
            if json.loads(self.ws.recv()).get('op') != 2:
                raise RuntimeError('OBS WebSocket identification failed')
        except BaseException:
            self.ws.close()
            raise

    def call(self, kind, **data):
        request_id = uuid.uuid4().hex
        self.ws.send(json.dumps({'op': 6, 'd': {
            'requestType': kind, 'requestId': request_id, 'requestData': data}}))
        while True:
            response = json.loads(self.ws.recv())
            if response.get('op') != 7 or response['d']['requestId'] != request_id:
                continue
            payload = response['d']
            if not payload['requestStatus']['result']:
                raise ObsRequestError(kind, payload['requestStatus'])
            return payload.get('responseData', {})

    def close(self):
        self.ws.close()


def ensure_input(obs, name, kind, settings, enabled):
    inputs = obs.call('GetInputList')['inputs']
    if not any(item['inputName'] == name for item in inputs):
        return obs.call('CreateInput', sceneName=SCENE, inputName=name,
                        inputKind=kind, inputSettings=settings,
                        sceneItemEnabled=enabled)['sceneItemId']
    current = obs.call('GetInputSettings', inputName=name)['inputSettings']
    if any(current.get(key) != value for key, value in settings.items()):
        obs.call('SetInputSettings', inputName=name, inputSettings=settings, overlay=True)
    return obs.call('GetSceneItemId', sceneName=SCENE, sourceName=name)['sceneItemId']


def configure(obs):
    if not any(s['sceneName'] == SCENE for s in obs.call('GetSceneList')['scenes']):
        obs.call('CreateScene', sceneName=SCENE)
    # V4L2 encodes (width, height) as a pair of 32-bit integers. Request the
    # camera's native 720p MJPEG mode, rather than its 8-fps uncompressed mode.
    camera_id = ensure_input(obs, CAMERA, 'v4l2_input', {
        'device_id': os.environ.get('HANDSPARK_CAMERA_DEVICE', '/dev/video0'), 'input': 0,
        'pixelformat': int.from_bytes(b'MJPG', 'little'),
        'resolution': (1280 << 32) | 720,
        'framerate': (1 << 32) | 30, 'buffering': False,
    }, True)
    overlays = {}
    for reaction, name in REACTIONS.items():
        overlays[reaction] = ensure_input(obs, name, 'ffmpeg_source', {
            'is_local_file': True, 'local_file': str(ASSET_DIR / (reaction + '.mov')),
            'looping': False, 'restart_on_activate': True,
            'clear_on_media_end': True, 'close_when_inactive': True,
            'hw_decode': False,
        }, False)
    for item in (camera_id, *overlays.values()):
        obs.call('SetSceneItemTransform', sceneName=SCENE, sceneItemId=item,
                 sceneItemTransform={'positionX': 0.0, 'positionY': 0.0,
                                     'alignment': 5, 'boundsType': 'OBS_BOUNDS_SCALE_INNER',
                                     'boundsAlignment': 0, 'boundsWidth': 1280.0,
                                     'boundsHeight': 720.0})
    obs.call('SetSceneItemEnabled', sceneName=SCENE, sceneItemId=camera_id, sceneItemEnabled=True)
    for item in overlays.values():
        obs.call('SetSceneItemEnabled', sceneName=SCENE, sceneItemId=item, sceneItemEnabled=False)
    obs.call('SetCurrentProgramScene', sceneName=SCENE)
    # Virtual webcams carry video only. OBS must not monitor or capture any
    # microphone; Teams continues using its existing microphone directly.
    for name in obs.call('GetSpecialInputs').values():
        if name:
            obs.call('SetInputMute', inputName=name, inputMuted=True)
    if not obs.call('GetVirtualCamStatus')['outputActive']:
        obs.call('StartVirtualCam')
    for _ in range(20):
        if obs.call('GetVirtualCamStatus')['outputActive']:
            break
        time.sleep(0.1)
    else:
        raise RuntimeError('OBS kon de virtuele camera niet starten; controleer het OBS-logboek')
    return overlays


def fire(obs, overlays, reaction, anchor=None):
    reference = ANCHOR_REFERENCE.get(reaction, (0.0, 0.0))
    anchor = anchor or DEFAULT_ANCHOR.get(reaction, (0.0, 0.0))
    obs.call('SetSceneItemTransform', sceneName=SCENE, sceneItemId=overlays[reaction],
             sceneItemTransform={'positionX': (anchor[0] - reference[0]) * 1280,
                                 'positionY': (anchor[1] - reference[1]) * 720})
    for key, item in overlays.items():
        obs.call('SetSceneItemEnabled', sceneName=SCENE, sceneItemId=item,
                 sceneItemEnabled=key == reaction)
    obs.call('TriggerMediaInputAction', inputName=REACTIONS[reaction],
             mediaAction='OBS_WEBSOCKET_MEDIA_INPUT_ACTION_RESTART')
    LOG.info('Gebarenreactie gestart: %s', reaction)


def recognize(obs, overlays, stopping):
    import mediapipe as mp
    import numpy as np
    from PIL import Image
    from control import Control
    from matte import BACKGROUND_REACTIONS, PersonMatte
    import queue

    saved = load_settings()
    settings = {key: saved[key] for key in ('automatic', 'depth')}

    options = mp.tasks.vision.HandLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=str(BASE / 'hand_landmarker.task')),
        running_mode=mp.tasks.vision.RunningMode.VIDEO, num_hands=2,
        min_hand_detection_confidence=0.6,
        min_hand_presence_confidence=0.6, min_tracking_confidence=0.5)
    gate = ReactionTrigger(cooldown=6.0)
    control = Control()
    matte = PersonMatte(obs, CAMERA, SCENE)
    active = None
    hide_at = 0.0
    last_timestamp = -1
    last_preview = 0.0
    rgb = None
    raw_hands = []

    def clear_effect():
        nonlocal active, hide_at
        for item in overlays.values():
            obs.call('SetSceneItemEnabled', sceneName=SCENE, sceneItemId=item, sceneItemEnabled=False)
        if matte.enabled:
            matte.show(False)
        active, hide_at = None, 0.0

    def start_effect(reaction, now, anchor=None, manual=False):
        nonlocal active, hide_at
        behind = settings['depth'] and reaction in BACKGROUND_REACTIONS
        if behind and rgb is not None:
            matte.update(rgb, raw_hands)
        fire(obs, overlays, reaction, anchor)
        active, hide_at = reaction, now + 5.05
        if behind and rgb is not None:
            matte.show(True)
        elif matte.enabled:
            matte.show(False)
        if manual:
            gate.suppress(now, reaction)

    with mp.tasks.vision.HandLandmarker.create_from_options(options) as landmarker:
        video = obs.call('GetVideoSettings')
        control.update(**settings, output_resolution=video['outputHeight'],
                       output_fps=video['fpsNumerator'] / video['fpsDenominator'])
        control.start()
        LOG.info('Klaar: acht gebaren, diepte-effecten en lokale camerabediening')
        address = os.environ.get('NOTIFY_SOCKET')
        if address:
            if address.startswith('@'):
                address = '\0' + address[1:]
            with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as notifier:
                notifier.connect(address)
                notifier.sendall(b'READY=1\nSTATUS=Teams Effects camera, diepte-effecten en bediening zijn actief')
        try:
            while not stopping[0]:
                started = time.monotonic()
                try:
                    for _ in range(8):
                        try:
                            command = control.commands.get_nowait()
                        except queue.Empty:
                            break
                        kind = command['command']
                        if kind == 'react':
                            if command.get('reaction') in REACTIONS:
                                start_effect(command['reaction'], started, manual=True)
                        elif kind in settings:
                            settings[kind] = command['enabled']
                            update_settings(**{kind: settings[kind]})
                            gate.reset_candidate()
                            if kind == 'depth' and not settings['depth'] and matte.enabled:
                                matte.show(False)
                        elif kind == 'cancel':
                            clear_effect()
                            gate.suppress(started, cooldown=False)
                    if active and started >= hide_at:
                        clear_effect()
                    behind = settings['depth'] and active in BACKGROUND_REACTIONS
                    needs_hands = settings['automatic'] or behind
                    gesture = None
                    hands = []
                    if needs_hands:
                        screenshot = obs.call('GetSourceScreenshot', sourceName=CAMERA,
                                              imageFormat='jpg', imageWidth=640, imageHeight=360,
                                              imageCompressionQuality=85)['imageData']
                        with Image.open(io.BytesIO(base64.b64decode(screenshot.split(',', 1)[1]))) as image:
                            rgb = np.array(image.convert('RGB'))
                        timestamp = max(last_timestamp + 1, int(started * 1000))
                        last_timestamp = timestamp
                        result = landmarker.detect_for_video(
                            mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb), timestamp)
                        raw_hands = [[(p.x, p.y) for p in hand] for hand in result.hand_landmarks]
                        aspect = rgb.shape[1] / rgb.shape[0]
                        hands = [[(x * aspect, y) for x, y in hand] for hand in raw_hands]
                        gesture = classify(hands)
                    reaction = gate.update(gesture if settings['automatic'] else None, started)
                    if reaction and not active:
                        start_effect(reaction, started, reaction_anchor(reaction, hands, aspect))
                    if settings['depth'] and active in BACKGROUND_REACTIONS and rgb is not None:
                        matte.update(rgb, raw_hands)
                        if not matte.enabled:
                            matte.show(True)
                    now = time.monotonic()
                    if control.preview_until > now and now - last_preview >= 0.45:
                        preview = obs.call('GetSourceScreenshot', sourceName=SCENE,
                                           imageFormat='jpg', imageWidth=640, imageHeight=360,
                                           imageCompressionQuality=75)['imageData']
                        control.update(preview=preview)
                        last_preview = now
                    control.update(**settings, reaction=active,
                                   remaining=max(0.0, hide_at - now) if active else 0,
                                   candidate=gesture, progress=gate.progress(started),
                                   needs_release=not gate.armed and (gate.require_release or gesture == gate.last_reaction),
                                   hands=len(hands), cooldown=max(0, gate.last_fired + gate.cooldown - now),
                                   mask_frames=matte.generation, error=None, error_code=None)
                except (OSError, ValueError) as error:
                    # A lost OBS connection needs a restart rather than an endless
                    # warning loop that leaves a frozen virtual camera behind.
                    if isinstance(error, OSError) and not isinstance(error, ValueError):
                        raise
                    LOG.warning('Camerabeeld tijdelijk niet beschikbaar: %s', error)
                    control.update(error='frame_unavailable', error_code='frame_unavailable')
                time.sleep(max(0.0, 1 / 8 - (time.monotonic() - started)))
        finally:
            control.close()
            clear_effect()
            matte.close()


def run():
    parser = argparse.ArgumentParser()
    parser.add_argument('--reaction', choices=REACTIONS)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
    if args.reaction:
        from control import request
        request('react', reaction=args.reaction)
        return

    stopping = [False]
    for sig in (signal.SIGINT, signal.SIGTERM):
        signal.signal(sig, lambda *_: stopping.__setitem__(0, True))
    log_path = Path.home() / '.cache/teams-effects/obs.log'
    log_path.parent.mkdir(parents=True, exist_ok=True)
    obs = None
    child = None
    try:
        from bootstrap import configure_video
        configure_video()
        try:
            obs = Obs()
        except (OSError, websocket.WebSocketException):
            with log_path.open('ab') as log:
                child = subprocess.Popen([
                    '/usr/bin/obs', '--profile', SCENE, '--collection', SCENE,
                    '--disable-shutdown-check', '--disable-missing-files-check',
                    '--minimize-to-tray'], stdout=log, stderr=subprocess.STDOUT)
            for _ in range(80):
                if stopping[0]:
                    return
                if child.poll() is not None:
                    raise RuntimeError(f'OBS is gestopt; zie {log_path}')
                try:
                    obs = Obs()
                    break
                except (OSError, websocket.WebSocketException):
                    time.sleep(0.5)
            else:
                raise RuntimeError(f'OBS WebSocket niet bereikbaar; zie {log_path}')
        # The socket starts before OBS finishes loading its collection and
        # camera sources; wait for its frontend instead of racing scene load.
        for _ in range(80):
            try:
                obs.call('GetSceneList')
                break
            except ObsRequestError as error:
                if error.code != 207:
                    raise
                time.sleep(0.25)
        else:
            raise RuntimeError('OBS heeft zijn camerascene niet tijdig geladen')
        if (obs.call('GetProfileList')['currentProfileName'] != SCENE
                or obs.call('GetSceneCollectionList')['currentSceneCollectionName'] != SCENE):
            raise RuntimeError('Select the Teams Effects OBS profile and collection, or close OBS and restart HandSpark.')
        overlays = configure(obs)
        recognize(obs, overlays, stopping)
    finally:
        if obs:
            try:
                obs.call('StopVirtualCam')
            except Exception:
                pass
            obs.close()
        if child and child.poll() is None:
            child.terminate()
            try:
                child.wait(timeout=8)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()


if __name__ == '__main__':
    run()
