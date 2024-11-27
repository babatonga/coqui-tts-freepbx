import os
import argparse
import logging
from asterisk import read_transcriptions, prepare_tts, do_tts_asterisk, do_conversions, check_command_availability
from utils import test, initialize_tts

logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description='Generate TTS files')
    parser.add_argument('--test',
                        '-t',
                        action='store_true',
                        help='Generate TTS for a single text')
    
    parser.add_argument('--emotion',
                        '-e',
                        nargs='?',
                        default=None,
                        required=False,
                        help='Emotion to use for TTS (Check if supported by model).')
    
    parser.add_argument('--speed',
                        '-s',
                        nargs='?',
                        default=1.0,
                        type=float,
                        required=False,
                        help='Speed to use for TTS (Check if supported by model).')
    
    parser.add_argument('--model',
                        '-m',
                        nargs='?',
                        default='tts_models/de/thorsten/vits',
                        required=False,
                        help='Model to use for TTS (Check if supported by model).')
    
    parser.add_argument('--language',
                        '-l',
                        nargs='?',
                        default=None,
                        required=False,
                        help='Language to use for TTS (Check if supported by model).')
    
    parser.add_argument('text',
                        nargs='?',
                        type=str,
                        help='Text to generate TTS for, only used with --test')
    
    args = parser.parse_args()


    if args.test:
        if not args.text:
            parser.error("Testing TTS requires text to generate")
        logger.info(f"Running TTS to generate test sound file with model: {args.model} and language: {args.language} for text: {args.text}")
        initialize_tts(args.model)
        test(args.text, args.emotion, args.speed, args.language)
    else:
        check_command_availability('ffmpeg')
        check_command_availability('sox')
        logger.info(f"Running TTS to generate asterisk sound files from transcriptions with model: {args.model} and language: {args.language}")
        initialize_tts(args.model)
        transcriptions = read_transcriptions()
        tts_preparement = prepare_tts(transcriptions)
        created = do_tts_asterisk(tts_preparement, args.emotion, args.speed, args.language)
        logger.info(f"Done generating TTS files: {created} created")
        logger.info("Converting TTS files to asterisk formats")
        do_conversions()
        logger.info("Done converting TTS files to asterisk formats")
        logger.info("All done!")
    
if __name__ == '__main__':
    if not os.path.exists('logs'):
        os.makedirs('logs')
    logfilehandler = logging.FileHandler('logs/tts.log', encoding='utf-8')
    logfilehandler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - [%(levelname)s] - %(message)s'))
    consolehandler = logging.StreamHandler()
    consolehandler.setFormatter(logging.Formatter('%(asctime)s - [%(levelname)s] - %(message)s'))
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - [%(levelname)s] - %(message)s', handlers=[logfilehandler, consolehandler])
    logging.getLogger('TTS').setLevel(logging.ERROR)
    main()