# HaGRID thumb recognition

HandSpark combines a trained image classifier with its existing hand geometry.
MediaPipe still locates up to two hands. The classifier reads square RGB crops
around their landmarks at 128×128, using OpenCV DNN on the CPU. It supports thumbs
up/down and their two-hand reactions; the other gesture rules are unchanged.

A model score of at least 0.8 selects the image result. Scores are not calibrated
probabilities. `like` maps to thumbs up; `dislike` and the rotated `thumb_down`
class map to thumbs down. Confident other classes veto a geometric thumb result.
Uncertain predictions defer to geometry. Basic checks require the thumb to point
in the indicated direction and the hand to have folded fingers; clearly
outstretched fingers reject an image thumb prediction. Hold, release, cooldown
and duplicate-hand protection still apply.

The classifier does not save or upload images. The model is bundled in the
release and uses dependencies already in `requirements.lock`. If it is missing,
fails its checksum or fails inference, HandSpark uses geometric recognition.
`handspark status --json` reports `gesture_engine: "hagrid+geometry"` or
`"geometry"`. Model downloads occur during source setup/build, not during normal
use of the release package.

## Model provenance

The unchanged `crops_classifier.onnx` is from the HaGRID authors’ dynamic-gestures
repository, revision `557a836bf82fce8d36494d0c17e95ca236f5611c`:

https://github.com/ai-forever/dynamic_gestures

Its original label order, input normalization, pinned download URL and SHA-256
are recorded in `hagrid-model.json`. The file is 411,683 bytes. The upstream
repository’s Apache 2.0 license text is included in
`licenses/hagrid-APACHE-2.0.txt`; the model retains that license. HandSpark’s
original code remains MIT. The original HaGRID dataset has a separate custom
license and is not included. See `THIRD_PARTY_NOTICES.md`.

## Development checks

The integration was checked on public images from the downscaled HaGRID sample:

https://huggingface.co/datasets/cj-mills/hagrid-sample-30k-384p

Dataset revision: `40b00da827c57b98efb5bc73f5abf49307c713d4`.
For each of its 18 gesture classes, set A uses the first ten available image IDs
in lexicographic order. Set B selects the first ten while excluding all subject
IDs present in A. Each contains 180 images. Labels and boxes come from the
sample’s annotation index; boxes retain their original normalized coordinates.

MediaPipe runs with two hands and detection/presence thresholds of 0.6.
Detected hands match annotations by maximum intersection-over-union, requiring
at least 0.1. The comparison counts thumb decisions per matched hand: `like`
and `dislike` are positives and other labels are negatives. Crop padding is
1.2× the larger hand dimension. The ordinary runtime classifier and its pose
checks produce the combined decisions.

| Check | Matched thumb hands | Geometry correct | Combined correct | Non-thumb hands | Combined false thumb decisions |
| --- | ---: | ---: | ---: | ---: | ---: |
| Development A | 17 | 9 | 14 | 163 | 0 |
| Additional subjects B | 19 | 17 | 18 | 173 | 0 |

These are small development sanity checks, not an independent accuracy
benchmark. The open-hand guard was developed using A; B was checked afterward.
Upstream model training overlap is unknown. Tracking produced no landmarks on
23 images in A and 12 in B; those images are excluded from the hand-level table.
Unmatched hands are also excluded. These results do not measure temporal false
triggers, full video performance or an individual user’s recognition quality.

The automated tests separately cover RGB normalization, batching and invalid
crops, label/confidence handling, checksum enforcement, inference failure and
geometric fallback, two-hand priority, duplicate tracks, reaction placement and
the existing hold/cooldown behavior. CI prepares the pinned models and includes
a real-model CPU smoke test on a synthetic blank image.

## CPU cost

On an Intel Core i5-7300U with OBS running, a complete classifier call (crop,
resize, normalization and inference) measured:

| Hands in a batch | Median | 95th percentile |
| --- | ---: | ---: |
| One | 14.12 ms | 35.38 ms |
| Two | 31.77 ms | 49.36 ms |

This uses one OpenCV thread, ten warm-up calls and fifty measured calls on a
public positive sample; the two-hand timing duplicates that crop. CPU load and
power settings affect the result. These timings measure the added classifier,
not the complete camera pipeline. Gesture recognition remains sampled at up to
8 Hz, independently of the preview and the configured 30-fps camera output.
