import streamlit as st
import ffmpeg
import io
import os
import tempfile

st.set_page_config(page_title="Song Extender AI", layout="centered")
st.title("🎵 Extend a Section of a Song Seamlessly")

uploaded_file = st.file_uploader("Upload your MP3 file", type=["mp3"])

def time_to_seconds(t):
    parts = t.strip().split(":")
    return int(parts[0]) * 60 + int(parts[1])

if uploaded_file:
    start_time = st.text_input("Start time (e.g. 2:30)", "2:30")
    end_time = st.text_input("End time (e.g. 2:40)", "2:40")
    new_duration_sec = st.number_input("How long should this section be after extension? (in seconds)", min_value=5, step=1, value=20)

    if st.button("🔁 Extend Section"):
        with st.spinner("Processing..."):
            try:
                with tempfile.TemporaryDirectory() as tmpdir:
                    input_path = os.path.join(tmpdir, "input.mp3")
                    with open(input_path, "wb") as f:
                        f.write(uploaded_file.read())

                    s_sec = time_to_seconds(start_time)
                    e_sec = time_to_seconds(end_time)
                    section_duration = e_sec - s_sec

                    # Create temporary output paths
                    before_path = os.path.join(tmpdir, "before.mp3")
                    looped_path = os.path.join(tmpdir, "looped.mp3")
                    after_path = os.path.join(tmpdir, "after.mp3")
                    final_path = os.path.join(tmpdir, "output.mp3")

                    # Split before
                    ffmpeg.input(input_path, ss=0, to=s_sec).output(before_path).run(quiet=True, overwrite_output=True)

                    # Extract section to loop
                    ffmpeg.input(input_path, ss=s_sec, to=e_sec).output(looped_path).run(quiet=True, overwrite_output=True)

                    # Repeat section
                    loop_count = (new_duration_sec + section_duration - 1) // section_duration  # Round up
                    concat_list = '|'.join([looped_path]*loop_count)
                    extended_loop_path = os.path.join(tmpdir, "extended_loop.mp3")
                    os.system(f"ffmpeg -y -i "concat:{concat_list}" -t {new_duration_sec} -c copy {extended_loop_path}")

                    # Split after
                    ffmpeg.input(input_path, ss=e_sec).output(after_path).run(quiet=True, overwrite_output=True)

                    # Concatenate all
                    concat_txt = os.path.join(tmpdir, "concat.txt")
                    with open(concat_txt, "w") as f:
                        f.write(f"file '{before_path}'\n")
                        f.write(f"file '{extended_loop_path}'\n")
                        f.write(f"file '{after_path}'\n")

                    ffmpeg.input(concat_txt, format='concat', safe=0).output(final_path, c='copy').run(quiet=True, overwrite_output=True)

                    # Serve final audio
                    with open(final_path, "rb") as f:
                        st.success("✅ Here's your extended song:")
                        st.audio(f.read(), format='audio/mp3')

            except Exception as e:
                st.error(f"Error: {str(e)}")