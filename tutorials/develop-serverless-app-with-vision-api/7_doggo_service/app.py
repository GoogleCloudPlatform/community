import base64
import io
import os
import sys
from pathlib import Path

from flask import Flask, request, render_template, send_from_directory
from google.cloud import vision
from googleapiclient.discovery import build
from PIL import Image

app = Flask(__name__)


client = vision.ImageAnnotatorClient()
kgapi = build("kgsearch", "v1", developerKey=os.environ["KGSEARCH_API"])


@app.route("/<path:path>")
def send_img(path):
    return send_from_directory("", path)


def get_breeds(stream):
    bytesio = stream.read()
    image = vision.Image(content=bytesio)

    objects = client.object_localization(image=image).localized_object_annotations

    im = Image.open(io.BytesIO(bytesio))

    count = 0
    output = []
    for obj in objects:
        data = {}
        count += 1

        # split image
        box = [
            (vertex.x * im.width, vertex.y * im.height)
            for vertex in obj.bounding_poly.normalized_vertices
        ]
        item = im.crop((box[0][0], box[0][1], box[2][0], box[2][1]))

        # save cropped image to file, load into vision API
        item_io = io.BytesIO()
        item.save(item_io, format="png")

        item_bytes = item_io.getvalue()
        image = vision.Image(content=item_bytes)
        data["image"] = base64.b64encode(item_bytes).decode("utf-8")

        response = client.label_detection(image=image)

        labels = [label.description for label in response.label_annotations]
        descs = [label.description for label in response.label_annotations]
        mids = [label.mid for label in response.label_annotations]

        if "Dog" not in descs:
            continue

        # check MIDs
        response = kgapi.entities().search(ids=mids).execute()
        results = [resp["result"] for resp in response["itemListElement"]]
        breed = None
        for item in results:
            if "description" in item.keys() and item["description"] == "Dog breed":
                breed = item["name"]
                continue

        data["breed"] = breed if breed else None
        output.append(data)

    return output


@app.route("/", methods=["GET", "POST"])
def main():
    if request.method == "POST":
        if "file" in request.files:
            file = request.files["file"]
            if file.filename:
                data = get_breeds(file)
                if not data:
                    error = "Uploaded image contains no dogs"
                    title = "Sad doggo"
                else:
                    error = None
                    title = f"Good doggo{'s' if len(data) > 1 else ''}"
                return render_template(
                    "index.html", data=data, error=error, title=title
                )

    return render_template("index.html")


if __name__ == "__main__":
    app.run(host="localhost", port=8080, debug=True)
