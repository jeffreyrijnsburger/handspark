"""The eight documented Apple reaction mappings, rendered locally for OBS."""
from pathlib import Path

APPLE_REFERENCE = 'https://support.apple.com/nl-nl/105117'
ASSET_DIR = Path(__file__).resolve().parent / 'reactions-apple'
REACTIONS = {
    'heart': 'Hartjes bij twee handen',
    'balloons': 'Ballonnen bij een vredesteken',
    'thumbs_up': 'Duimpjes bij thumbs up',
    'thumbs_down': 'Duim omlaag',
    'rain': 'Regen bij twee duimen omlaag',
    'confetti': 'Confetti bij twee vredestekens',
    'fireworks': 'Vuurwerk bij twee duimen omhoog',
    'lasers': 'Lasers bij metal horns',
}
ALL_REACTIONS = {**REACTIONS, 'prosper': 'Orbitale groet'}
GESTURE_LABELS = {
    'heart': 'Hartje vormen met twee handen',
    'balloons': 'Een vredesteken (V)',
    'thumbs_up': 'Een duim omhoog',
    'thumbs_down': 'Een duim omlaag',
    'rain': 'Twee duimen omlaag',
    'confetti': 'Twee vredestekens (V)',
    'fireworks': 'Twee duimen omhoog',
    'lasers': 'Metal horns met beide handen',
}
ANCHOR_REFERENCE = {'heart': (0.5, 0.75), 'thumbs_up': (0.5, 0.5), 'thumbs_down': (0.5, 0.5)}
DEFAULT_ANCHOR = {'heart': (0.5, 0.75), 'thumbs_up': (0.78, 0.32), 'thumbs_down': (0.78, 0.32)}
