from pathlib import Path
from TTS.api import TTS
import torch
from datetime import datetime
import sys
import os
import logging
logger = logging.getLogger(__name__)

BASEDIR = Path(__file__).resolve().parent
OUTPUTDIR = BASEDIR / 'output'
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"

tts = None

def initialize_tts(model = "tts_models/de/thorsten/tacotron2-DDC"):
    global tts
    logger.info(f"Initalizing TTS with model: {model} on device: {DEVICE}")
    tts = TTS(model_name=model).to(DEVICE)


def do_tts(text, output_path, emotion=None, speed: float = 1.0, language=None):
    if tts is None:
        initialize_tts()
    short_text = text[:10] + "..." if len(text) > 10 else text
    logger.debug(f"Generating TTS for: {short_text} to: {output_path} with emotion: {emotion} and speed: {speed}")
    try:
        tts.tts_to_file(text=text, file_path=output_path, emotion=emotion, speed=speed, split_sentences=True, language=language)
    except Exception as e:
        logger.error(f"Error generating TTS for: {short_text}", exc_info=e, stack_info=True)
        sys.exit(1)


def test(text, emotion, speed, language=None):
    date = datetime.now().strftime("%Y%m%d%H%M%S")
    short_text = text[:20] if len(text) > 20 else text
    sanitized_filename = ''.join(e for e in short_text if e.isalnum())
    output_path = Path(OUTPUTDIR, "test", f"{date}-{sanitized_filename}.wav")
    if not output_path.parent.exists():
        output_path.parent.mkdir(parents=True, exist_ok=True)
    do_tts(text, output_path, emotion, speed, language)


