import streamlit as st
import ffmpeg
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

                    # Paths
                    before_path = os.path.join(tmpdir, "before.mp3")
                    section_path = os.path.join(tmpdir, "section.mp3")
                    after_path = os.path.join(tmpdir, "after.mp3")
                    extended_section_path = os.path.join(tmpdir, "extended_section.mp3")
                    final_path = os.path.join(tmpdir, "output.mp3")

                    # Extract before, section, and after
                    ffmpeg.input(input_path, ss=0, to=s_sec).output(before_path).run(overwrite_output=True, quiet=True)
                    ffmpeg.input(input_path, ss=s_sec, to=e_sec).output(section_path).run(overwrite_output=True, quiet=True)
                    ffmpeg.input(input_path, ss=e_sec).output(after_path).run(overwrite_output=True, quiet=True)

                    # Determine repeat count
                    repeat_count = max(1, round(new_duration_sec / section_duration))

                    # Create concat list file for repeated section
                    section_list_txt = os.path.join(tmpdir, "section_list.txt")
                    with open(section_list_txt, "w") as f:
                        for _ in range(repeat_count):
                            f.write(f"file '{section_path}'\n")

                    # Concatenate repeated section
                    ffmpeg.input(section_list_txt, format='concat', safe=0).output(extended_section_path, c='copy').run(overwrite_output=True, quiet=True)

                    # Create final concat list
                    final_concat_list = os.path.join(tmpdir, "final_concat.txt")
                    with open(final_concat_list, "w") as f:
                        f.write(f"file '{before_path}'\n")
                        f.write(f"file '{extended_section_path}'\n")
                        f.write(f"file '{after_path}'\n")

                    # Generate final output
                    ffmpeg.input(final_concat_list, format='concat', safe=0).output(final_path, c='copy').run(overwrite_output=True, quiet=True)

                    # Serve final audio
                    with open(final_path, "rb") as f:
                        st.success("✅ Here's your extended song:")
                        st.audio(f.read(), format='audio/mp3')

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")