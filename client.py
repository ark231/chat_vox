#!/usr/bin/env python3

import sys
import requests
import io
import wave
import sounddevice as sd
import numpy as np
from base64 import b64decode
import toml
from pathlib import Path


class ChatVoxClient:
    def __init__(self, server_base_url: str = "http://localhost:55000"):
        self.server_base_url = server_base_url

    def send_message(self, message: str):
        payload = {"message": message}
        response = requests.post(f"{self.server_base_url}/talk", params=payload)
        if not response.ok:
            print(f"error: POST to {self.server_base_url}/talk returned {response.status_code}", file=sys.stderr)
            sys.exit(1)
        print(f"ずんだもん> {response.json()['message']}")
        audio_data = io.BytesIO(b64decode(response.json()["voice"]))
        # io.BytesIOに格納された音声データを読み込む
        with wave.open(audio_data, "rb") as wav_file:
            data = wav_file.readframes(wav_file.getnframes())
            rate = wav_file.getframerate()

        # バイトストリームからnumpy配列に変換する
        samples = np.frombuffer(data, dtype=np.int16)

        # 再生する
        sd.play(samples, rate)
        sd.wait()


def main():
    config = toml.load(Path(__file__).parent / "config.toml")
    client = ChatVoxClient(config["server_base_url"])
    while True:
        try:
            message = input("you> ")
        except EOFError:
            message = ""
        if message == "":
            break
        client.send_message(message)


if __name__ == "__main__":
    main()
