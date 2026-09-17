"""Offline smoke check for the WebRTC spike's /offer handshake.

Uses aiortc as a fake browser client, entirely in-process -- no real mic,
no network, no manual browser step. This only proves the SDP offer/answer
plumbing works; it does NOT answer the Render UDP/ICE question (that needs
a real deploy and a real cross-network browser, per the decision doc).

Run: python spike/test_webrtc_offer.py
"""

import asyncio

from aiohttp.test_utils import TestClient, TestServer
from aiortc import RTCPeerConnection

from spike.webrtc_offer import build_app


async def _fake_offer_has_answer() -> None:
    server = TestServer(build_app())
    client = TestClient(server)
    await client.start_server()
    try:
        pc = RTCPeerConnection()
        pc.addTransceiver("audio", direction="sendrecv")
        offer = await pc.createOffer()
        await pc.setLocalDescription(offer)

        resp = await client.post(
            "/offer", json={"sdp": pc.localDescription.sdp, "type": pc.localDescription.type}
        )
        assert resp.status == 200, f"expected 200, got {resp.status}: {await resp.text()}"
        answer = await resp.json()
        assert answer["type"] == "answer", f"expected an SDP answer, got: {answer}"
        assert "sdp" in answer and len(answer["sdp"]) > 0, "answer has no SDP body"

        await pc.setRemoteDescription(
            type("Desc", (), {"sdp": answer["sdp"], "type": answer["type"]})()
        )
        # Let aiortc's ICE task actually start before close() tears down the
        # transport out from under it -- otherwise it logs a benign but noisy
        # "Task exception was never retrieved" on the in-progress connect.
        await asyncio.sleep(0.2)
        await pc.close()
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(_fake_offer_has_answer())
    print("ok: /offer returns a valid SDP answer")
