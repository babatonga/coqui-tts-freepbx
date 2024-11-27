import re
import os
import sys
import subprocess
from utils import *
from pathlib import Path
from tqdm import tqdm

logger = logging.getLogger(__name__)
TTSOUTPUTDIR = Path(OUTPUTDIR, 'asterisk')
TRANSCRIPTIONS_PATH = Path(__file__).resolve().parent / 'transcriptions'

def read_transcriptions():
    specialExpressions = r'\[.*\]|\(.*\)|\<.*\>|\.\.\.'
    ignoreLinesStartingWith = re.compile(r'^#|^/|^;')
    transcriptions = []
    for file in tqdm(os.listdir(TRANSCRIPTIONS_PATH), desc='Reading transcriptions', unit='file'):
        if file.endswith('.txt'):
            foldername = Path(file).stem
            try:
                with open(Path(TRANSCRIPTIONS_PATH, file), 'r', encoding='UTF-8') as f:
                    texts = []
                    for line in f:
                        if ignoreLinesStartingWith.match(line):
                            logger.debug(f"Skipping line: {line} in file: {file} as it starts with a comment character")
                            continue
                        linesplit = line.split(':', 1)
                        if len(linesplit) < 2:
                            logger.debug(f"Skipping line: {line} in file: {file} as it does not contain a colon")
                            continue
                        text_id = linesplit[0].strip()
                        if not text_id:
                            logger.debug(f"Skipping line: {line} in file: {file} as it does not contain a text id")
                            continue
                        text = linesplit[1].strip()
                        if not text:
                            logger.debug(f"Skipping line: {line} in file: {file} as it does not contain any text")
                            continue
                        text = re.sub(specialExpressions, '', text).strip()
                        # Workaround: Check if only single special character is present in the text
                        if len(text) == 1 and not text.isalnum():
                            logger.debug(f"Skipping line: {line} in file: {file} as it only contains a special character")
                            continue
                        if not text:
                            logger.debug(f"Skipping line: {line} in file: {file} as it does not contain any text")
                            continue
                        texts.append({
                            'id': text_id,
                            'text': text
                        })
                    transcriptions.append({
                        'folder': foldername,
                        'texts': texts
                    })
                    logger.debug(f"Read {len(texts)} transcriptions from file: {file}")
            except Exception as e:
                logger.error(f"Error reading file: {file}", exc_info=e, stack_info=True)
                sys.exit(1)
    return transcriptions

def prepare_tts(transcriptions):
    tts_preparement = []
    
    if not TTSOUTPUTDIR.exists():
        TTSOUTPUTDIR.mkdir(parents=True, exist_ok=True)

    for transcription in tqdm(transcriptions, desc='Preparing TTS', unit='folder'):
        for text in tqdm(transcription['texts'], desc=f'Folder {transcription["folder"]}', unit='file'):
            file_path = Path(TTSOUTPUTDIR, transcription['folder'], text['id'] + '.wav')
            folder_path = file_path.parent
            file = file_path.name
            if not folder_path.exists():
                folder_path.mkdir(parents=True, exist_ok=True)
            tts_preparement.append({
                'path': Path(folder_path, file),
                'text': text['text']
            })
    return tts_preparement

def do_tts_asterisk(tts_preparement, emotion=None, speed:float = 1.0 , language=None):
    created = 0

    for tts in tqdm(tts_preparement, desc='Generating TTS', unit='file'):
        do_tts(tts['text'], tts['path'])
        created += 1
    return created

def check_command_availability(command):
    """Check if a command is available in the system."""
    try:
        subprocess.run([command, '--help'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except FileNotFoundError:
        logger.error(f"{command} is not installed or not in PATH. Please install it before running this script.")
        exit(1)

def process_file(file_path: Path):
    """Process a single .wav file to remove silence, normalize, and convert to multiple formats."""
    file_no_ext = file_path.with_suffix('')

    # Remove silence and normalize
    file_silence_removed = file_no_ext.with_name(f"{file_no_ext.stem}_silence_removed.wav")
    logger.debug(f"Removing silence from {file_path}")
    subprocess.run([
        'sox', '-V', str(file_path), str(file_silence_removed),
        'silence', '1', '0.1', '1%', '-1', '0.1', '1%'
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

    # Fade in, fade out, and pad
    file_fade = file_no_ext.with_name(f"{file_no_ext.stem}_fade.wav")
    logger.debug(f"Applying fade in/out to {file_silence_removed}")
    subprocess.run([
        'sox', '-V', str(file_silence_removed), str(file_fade),
        'norm', '-3', 'fade', 't', '0.02', '-0.02', 'pad', '0.02', '0.02'
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

    # Remove intermediate silence removed file
    os.remove(file_silence_removed)

    # Conversion commands
    conversions = [
        (['sox', '-V', str(file_fade), '-r', '8000', '-c', '1', '-t', 'al', f"{file_no_ext}.alaw"], "ALAW"),
        (['sox', '-V', str(file_fade), '-r', '8000', '-c', '1', '-t', 'ul', f"{file_no_ext}.ulaw"], "ULAW"),
        (['ffmpeg', '-y', '-i', str(file_fade), '-ar', '16000', '-ac', '1', '-acodec', 'g722', f"{file_no_ext}.g722"], "G.722"),
        (['sox', '-V', str(file_fade), '-r', '8000', '-c', '1', '-t', 'gsm', f"{file_no_ext}.gsm"], "GSM"),
        (['sox', str(file_fade), '-t', 'raw', '-r', '16000', '-c', '1', f"{file_no_ext}.sln16"], "SLN16"),
        (['sox', str(file_fade), '-t', 'raw', '-r', '48000', '-c', '1', f"{file_no_ext}.sln48"], "SLN48"),
    ]

    for command, format_name in conversions:
        logger.debug(f"Converting {file_fade} to {format_name}")
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

    # Replace original file with the processed file
    logger.debug(f"Replacing original file {file_path} with processed file {file_fade}")
    os.replace(file_fade, file_path)

def do_conversions(out_dir = TTSOUTPUTDIR):
    """Main function to process all .wav files under the out_dir/ directory."""
    # Check dependencies
    check_command_availability('sox')
    check_command_availability('ffmpeg')

    if not out_dir.exists() or not out_dir.is_dir():
        logger.error(f"Directory {out_dir} does not exist or is not a directory.")
        exit(1)

    # Find all .wav files recursively
    wav_files = list(out_dir.rglob('*.wav'))

    if not wav_files:
        logger.info(f"No .wav files found in {out_dir}")
        return
    
    # check if already processed files are present in out_dir
    suffixes = ['.alaw', '.ulaw', '.g722', '.gsm', '.sln16', '.sln48']
    processed_files = [f.with_suffix('') for f in wav_files if any(f.with_suffix(suffix).exists() for suffix in suffixes)]
    if processed_files:
        proceed = input("There are already processed files in the output directory. Proceeding could lead to corruption and bad quality. It is recommended to remove all output/asterisk files and re-run the script. Do you still want to proceed without cleaning output dir? (y/n): ")
        if proceed.lower() not in ['y', 'yes', 'j', 'ja']:
            logger.info("Exiting script.")
            exit(0)
        


    for wav_file in tqdm(wav_files, desc='Transcoding files', unit='file'):
        logger.debug(f"Processing file: {wav_file}")
        try:
            process_file(wav_file)
        except subprocess.CalledProcessError as e:
            logger.error(f"Error processing {wav_file}: {e}")