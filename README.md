# Generate Coqui-TTS Sound Files for Asterisk

## Status: Work in Progress (WIP)

This project facilitates the creation of high-quality sound files for Asterisk using Coqui-TTS. It supports various audio formats and offers configurable options for different TTS models and languages.

## Prerequisites

Before you begin, ensure the following dependencies are installed:

- **ffmpeg**: [https://www.ffmpeg.org/](https://www.ffmpeg.org/)
- **sox**: [https://sourceforge.net/projects/sox/](https://sourceforge.net/projects/sox/)
- **Python 3**: Supported versions are >= 3.9 and < 3.13.
- Additional dependencies might be required depending on the chosen TTS model and operating system (e.g., `espeak-ng` for certain configurations).

## Usage Instruction (use prebuild sounds)
See [wiki: Installing Sound Files in FreePBX](https://github.com/babatonga/coqui-tts-freepbx/wiki/Installing-Sound-Files-in-FreePBX)


## Usage Instructions (build your own)

### Getting Started
Currently, the script has been tested only for German text. The recommended model for optimal results is `"tts_models/de/thorsten/vits"`. While `"tts_models/de/thorsten/tacotron2-DDC"` provides a richer sound quality, it may crash when processing short words (see Known Issues below).

1. **Set up the environment:**
   - Create a Python virtual environment (venv), activate it, and install the dependencies listed in `requirements.txt`.

2. **Prepare your transcriptions:**
   - Place your transcription files in the `asterisk/transcriptions` directory. Sample German transcription files from the [joni1802/asterisk-sound-generator](https://github.com/joni1802/asterisk-sound-generator) project are included.

3. **Test the script:**
   - **For German:** Run the following command and verify that the output file `output/test/xxx.wav` is generated successfully:
     ```bash
     python text-to-speech.py --test "Dies ist ein einfacher Test"
     ```
   - **For other languages:** Run:
     ```bash
     python text-to-speech.py --model "tts_models/xx/my/model/path" --test "My test phrase"
     ```
     Add the `--language XX` flag if using a multilingual model. Verify that the output file `output/test/xxx.wav` is generated correctly.

4. **Generate audio files:**
   - Once testing is successful, run the following command to process your transcriptions:
     ```bash
     python text-to-speech.py
     ```
     Add relevant flags for model, language, and other parameters as needed. The script will generate files in multiple formats (`wav`, `alaw`, `ulaw`, `gsm`, `sln16`, `sln48`, and `g722`) and save them in the `output/asterisk` directory.


## Possible args:
```
usage: text-to-speech.py [-h] [--test] [--emotion [EMOTION]] [--speed [SPEED]] [--model [MODEL]] [--language [LANGUAGE]] [text]

Generate TTS files

positional arguments:
  text                  Text to generate TTS for, only used with --test

options:
  -h, --help            show this help message and exit
  --test, -t            Generate TTS for a single text
  --emotion [EMOTION], -e [EMOTION]
                        Emotion to use for TTS (Check if supported by model).
  --speed [SPEED], -s [SPEED]
                        Speed to use for TTS (Check if supported by model).
  --model [MODEL], -m [MODEL]
                        Model to use for TTS (Check if supported by model).
  --language [LANGUAGE], -l [LANGUAGE]
                        Language to use for TTS (Check if supported by model).
```

## Known Issues

1. **Short Words:** 
   - Certain models, such as `"tts_models/de/thorsten/tacotron2-DDC"`, may encounter errors or crashes when processing very short words (e.g., the German word "Elf").

2. **Audio Processing:**
   - To enhance audio quality, the script removes leading and trailing silence, applies fade-in and fade-out effects, and adds a short silence at both ends. However, these adjustments may cause issues with very short audio files, potentially requiring manual adjustments in the `asterisk.process_file()` conversion list.

Feel free to contribute or report issues to improve the project!
