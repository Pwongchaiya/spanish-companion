# Standalone image for the WebRTC signaling spike -- deliberately NOT the
# main app's Dockerfile/image. This answers one question only: does
# aiortc build here, and does Render's networking pass the ICE/UDP traffic
# an external browser needs. See spike/webrtc_offer.py and
# Projects/spanish-companion/decisions/voice-conversation-browser-webrtc-transport.md.
#
# No portaudio/pyaudio here on purpose -- this uses SmallWebRTCTransport,
# not LocalAudioTransport, so [local] is not in spike/requirements.txt and
# this image needs none of the main Dockerfile's native-audio build deps.
# aiortc's own native dependency (the `av` package) ships manylinux wheels,
# so no apt-get build toolchain is expected to be needed -- if this build
# fails on Render specifically, THAT is the answer to open question 1 in
# the decision doc, not a bug to silently work around.

FROM python:3.12-slim
WORKDIR /app

COPY spike/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY spike/ spike/

ENV PYTHONUNBUFFERED=1
ENV PORT=10000
EXPOSE 10000

CMD ["python", "-m", "spike.webrtc_offer"]
