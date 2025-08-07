import streamlit as st
import ffmpeg
import os
import tempfile
import base64
import requests

st.set_page_config(page_title="AI Music Extender", layout="centered")
st.title("🎶 AI Music Section Extender with MusicGen (Replicate API)")

uploaded_file = st.file_uploader("Upload your MP3 file", type=["mp3"])
replicate_api_token = st.text_input("Paste your Replicate API token (keep private)", type="password")

def time_to_seconds(t):
    parts = t.strip().split(":")
    return int(parts[0]) * 60 + int(parts[1])

def call_musicgen(audio_path, duration, api_token):
    with open(audio_path, "rb") as f:
        b64_audio = base64.b64encode(f.read()).decode("utf-8")

    headers = {
        "Authorization": f"Token {api_token}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        "https://api.replicate.com/v1/predictions",
        headers=headers,
        json={
            "version": "fb9e8d05c43c72d3e65faddb7ec5e3b7e2e750ec98e15de0f6ed6b8cf67f3c4c",
            "input": {
                "audio": b64_audio,
                "duration": duration
            }
        }
    )

    if response.status_code != 201:
        raise Exception(f"Replicate API error: {response.text}")

    prediction = response.json()
    prediction_url = prediction["urls"]["get"]

    # Poll until complete
    while True:
        poll_resp = requests.get(prediction_url, headers=headers)
        result = poll_resp.json()
        if result["status"] == "succeeded":
            return result["output"]
        elif result["status"] == "failed":
            raise Exception("MusicGen generation failed.")
        st.info("⏳ Generating music...")
        import time
        time.sleep(3)

if uploaded_file and replicate_api_token:
    start_time = st.text_input("Start time (e.g. 2:30)", "2:30")
    end_time = st.text_input("End time (e.g. 2:40)", "2:40")
    new_duration_sec = st.number_input("How long should this section be after extension? (in seconds)", min_value=5, step=1, value=20)

    if st.button("Generate AI Extension"):
        with st.spinner("Processing and contacting MusicGen..."):
            try:
                with tempfile.TemporaryDirectory() as tmpdir:
                    input_path = os.path.join(tmpdir, "input.mp3")
                    with open(input_path, "wb") as f:
                        f.write(uploaded_file.read())

                    s_sec = time_to_seconds(start_time)
                    e_sec = time_to_seconds(end_time)

                    before_path = os.path.join(tmpdir, "before.mp3")
                    section_path = os.path.join(tmpdir, "section.mp3")
                    after_path = os.path.join(tmpdir, "after.mp3")
                    ai_generated_path = os.path.join(tmpdir, "ai_section.mp3")
                    final_path = os.path.join(tmpdir, "output.mp3")

                    ffmpeg.input(input_path, ss=0, to=s_sec).output(before_path).run(overwrite_output=True, quiet=True)
                    ffmpeg.input(input_path, ss=s_sec, to=e_sec).output(section_path).run(overwrite_output=True, quiet=True)
                    ffmpeg.input(input_path, ss=e_sec).output(after_path).run(overwrite_output=True, quiet=True)

                    st.info("🔗 Sending audio section to Replicate MusicGen...")
                    ai_url = call_musicgen(section_path, new_duration_sec, replicate_api_token)

                    r = requests.get(ai_url)
                    with open(ai_generated_path, "wb") as f:
                        f.write(r.content)

                    concat_list_path = os.path.join(tmpdir, "concat.txt")
                    with open(concat_list_path, "w") as f:
                        f.write(f"file '{before_path}'\n")
                        f.write(f"file '{ai_generated_path}'\n")
                        f.write(f"file '{after_path}'\n")

                    ffmpeg.input(concat_list_path, format='concat', safe=0).output(final_path, c='copy').run(overwrite_output=True, quiet=True)

                    with open(final_path, "rb") as f:
                        st.success("✅ Here's your AI-extended track:")
                        st.audio(f.read(), format="audio/mp3")

            except Exception as e:
                st.error(f"❌ Error: {str(e)}")