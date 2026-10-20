"""Stream composed JPEG previews without opening the meeting camera device."""
import argparse
import base64
import sys
import time

from controller import Obs, SCENE
from settings import PREVIEW_FPS, PREVIEW_RESOLUTIONS


def frames(obs, resolution, fps, clock=time.monotonic, sleep=time.sleep):
    if type(resolution) is not int or resolution not in PREVIEW_RESOLUTIONS:
        raise ValueError('Unsupported preview resolution')
    if type(fps) is not int or fps not in PREVIEW_FPS:
        raise ValueError('Unsupported preview frame rate')
    height = min(resolution, obs.call('GetVideoSettings')['outputHeight'])
    while True:
        started = clock()
        data = obs.call('GetSourceScreenshot', sourceName=SCENE, imageFormat='jpg',
                        imageWidth=height * 16 // 9, imageHeight=height,
                        imageCompressionQuality=70)['imageData']
        yield base64.b64decode(data.split(',', 1)[1], validate=True)
        sleep(max(0, 1 / fps - (clock() - started)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--resolution', type=int, choices=PREVIEW_RESOLUTIONS, required=True)
    parser.add_argument('--fps', type=int, choices=PREVIEW_FPS, required=True)
    args = parser.parse_args()
    obs = None
    try:
        obs = Obs()
        for frame in frames(obs, args.resolution, args.fps):
            sys.stdout.buffer.write(frame)
            sys.stdout.buffer.flush()
    except BrokenPipeError:
        return 0
    except Exception:
        # Credentials and frame payloads never belong in a process log.
        print('Composed preview temporarily unavailable', file=sys.stderr)
        return 1
    finally:
        if obs:
            obs.close()


if __name__ == '__main__':
    raise SystemExit(main())
