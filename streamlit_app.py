import streamlit as st
import ffmpeg
import librosa
import soundfile as sf
import os
import tempfile

st.set_page_config(page_title="Song Extender AI", layout="centered")
st.title("🎵 Extend a Section of a Song Seamlessly (Beat-Aligned)")

uploaded_file = st.file_uploader("Upload your MP3 file", type=["mp3"])

def time_to_seconds(t):
    parts = t.strip().split(":")
    return int(parts[0]) * 60 + int(parts[1])

def snap_to_nearest_beat(times, target_time):
    return min(times, key=lambda t: abs(t - target_time))

if uploaded_file:
    start_time = st.text_input("Start time (e.g. 2:30)", "2:30")
    end_time = st.text_input("End time (e.g. 2:40)", "2:40")
    new_duration_sec = st.number_input("How long should this section be after extension? (in seconds)", min_value=5, step=1, value=20)

    if st.button("🔁 Extend Section"):
        with st.spinner("Analyzing and Processing..."):
            try:
                with tempfile.TemporaryDirectory() as tmpdir:
                    input_path = os.path.join(tmpdir, "input.mp3")
                    wav_path = os.path.join(tmpdir, "converted.wav")

                    with open(input_path, "wb") as f:
                        f.write(uploaded_file.read())

                    # Convert MP3 to WAV for librosa
                    ffmpeg.input(input_path).output(wav_path).run(overwrite_output=True, quiet=True)

                    # Beat tracking with librosa
                    y, sr = librosa.load(wav_path)
                    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
                    beat_times = librosa.frames_to_time(beat_frames, sr=sr)

                    # Snap input times to nearest beats
                    s_sec = time_to_seconds(start_time)
                    e_sec = time_to_seconds(end_time)
                    s_beat = snap_to_nearest_beat(beat_times, s_sec)
                    e_beat = snap_to_nearest_beat(beat_times, e_sec)

                    section_duration = e_beat - s_beat

                    # Export beat-aligned sections
                    before_path = os.path.join(tmpdir, "before.mp3")
                    section_path = os.path.join(tmpdir, "section.mp3")
                    after_path = os.path.join(tmpdir, "after.mp3")
                    extended_section_path = os.path.join(tmpdir, "extended_section.mp3")
                    final_path = os.path.join(tmpdir, "output.mp3")

                    ffmpeg.input(input_path, ss=0, to=s_beat).output(before_path).run(overwrite_output=True, quiet=True)
                    ffmpeg.input(input_path, ss=s_beat, to=e_beat).output(section_path).run(overwrite_output=True, quiet=True)
                    ffmpeg.input(input_path, ss=e_beat).output(after_path).run(overwrite_output=True, quiet=True)

                    # Repeat the section to reach desired duration
                    repeat_count = max(1, round(new_duration_sec / section_duration))
                    section_list_txt = os.path.join(tmpdir, "section_list.txt")
                    with open(section_list_txt, "w") as f:
                        for _ in range(repeat_count):
                            f.write(f"file '{section_path}'\n")

                    ffmpeg.input(section_list_txt, format='concat', safe=0).output(extended_section_path, c='copy').run(overwrite_output=True, quiet=True)

                    # Final concatenation
                    final_concat_list = os.path.join(tmpdir, "final_concat.txt")
                    with open(final_concat_list, "w") as f:
                        f.write(f"file '{before_path}'\n")
                        f.write(f"file '{extended_section_path}'\n")
                        f.write(f"file '{after_path}'\n")

                    ffmpeg.input(final_concat_list, format='concat', safe=0).output(final_path, c='copy').run(overwrite_output=True, quiet=True)

                    # Serve final song
                    with open(final_path, "rb") as f:
                        st.success("✅ Here's your extended, beat-aligned song:")
                        st.audio(f.read(), format='audio/mp3')

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")