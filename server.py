#!/usr/bin/env python3
import openai
import toml
import voicevox
import asyncio
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
import requests
from pathlib import Path
import json
from base64 import b64encode


PORT = 55000

VOICEVOX_BASE_URL = "http://localhost:50021"


async def speak_with_voicevox(text: str, style_id: int = 1):
    async with voicevox.Client(base_url=VOICEVOX_BASE_URL) as client:
        audio_query = await client.create_audio_query(text, speaker=style_id)
        return await audio_query.synthesis()


def response_talk(text: str, voice: bytes):
    return json.dumps({"message": text, "voice": b64encode(voice).decode(encoding="utf8")}).encode(encoding="utf8")


class RequestHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        # パスからクエリパラメータを取得する
        parsed_path = urlparse(self.path)
        query_params = dict([p.split("=") for p in parsed_path[4].split("&")]) if parsed_path[4] else {}

        # クエリパラメータから動作を判定する
        if parsed_path.path == "/talk":

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "あなたは、「ずんだもん」という名前のずんだ餅の妖精で、語尾に必ず「なのだー」とつけて話します。一人称は「ボク」で、二人称は「おまえ」です。また、この会話は友人との会話です。",
                    },
                    {"role": "user", "content": "おはよう"},
                    {"role": "assistant", "content": "おはようなのだー"},
                    {"role": "user", "content": query_params["message"]},
                ],
            )

            self.send_response(200)
            self.send_header("Content-type", "audio/wav")
            self.end_headers()
            returned_message = response["choices"][0]["message"]["content"]
            self.wfile.write(response_talk(returned_message, asyncio.run(speak_with_voicevox(returned_message))))
        else:
            # その他の場合は404 Not Foundを返す
            self.send_error(404, "Not Found")


def main():
    secrets = toml.load(Path(__file__).parent / "secrets.toml")
    openai.api_key = secrets["openai"]
    with HTTPServer(("", PORT), RequestHandler) as httpd:
        httpd.serve_forever()


if __name__ == "__main__":
    main()
