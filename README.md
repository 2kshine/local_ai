pip freeze > requirements.txt

extract audio and video 
ffmpeg -i videoplayback.mp4 -ss 00:10:00 -t 00:00:10 -c copy -avoid_negative_ts make_zero output_trimmed.mp4

source pythonenv/bin/activate
python3.10 -m venv pythonenv
