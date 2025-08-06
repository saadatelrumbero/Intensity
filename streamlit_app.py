import streamlit as st
from pydub import AudioSegment
import io
import tempfile
import math

st.set_page_config(page_title="Song Extender AI", layout="centered")
st.title("🎵 Extend a Section of a Song Seamlessly")

uploaded_file = st.file_uploader("Upload your MP3 file", type=["mp3"])

if uploaded_file:
    start_time = st.text_input("Start time (e.g. 2:30)", "2:30")
    end_time = st.text_input("End time (e.g. 2:40)", "2:40")
    new_duration_sec = st.number_input("How long should this section be after extension? (in seconds)", min_value=5, step=1, value=20)

    if st.button("🔁 Extend Section"):
        with st.spinner("Processing audio..."):
            try:
                # Load original MP3
                audio = AudioSegment.from_file(uploaded_file, format="mp3")

                # Convert time inputs to milliseconds
                def time_to_ms(t):
                    parts = t.strip().split(":")
                    return (int(parts[0]) * 60 + int(parts[1])) * 1000

                start_ms = time_to_ms(start_time)
                end_ms = time_to_ms(end_time)

                # Extract parts
                before = audio[:start_ms]
                section = audio[start_ms:end_ms]
                after = audio[end_ms:]

                # Calculate how many times to repeat
                section_duration = end_ms - start_ms
                repeat_count = math.ceil(new_duration_sec * 1000 / section_duration)
                extended_section = section * repeat_count
                extended_section = extended_section[:new_duration_sec * 1000]  # trim to exact

                # Rebuild the full song
                final = before + extended_section + after

                # Export to in-memory buffer
                buffer = io.BytesIO()
                final.export(buffer, format="mp3")
                buffer.seek(0)

                st.success("Done! Here's your extended song:")
                st.audio(buffer.read(), format='audio/mp3')

            except Exception as e:
                st.error(f"Error: {str(e)}")