import io
import os
import sys
from pathlib import Path

from google.cloud import vision
from googleapiclient.discovery import build
from PIL import Image
from flask import Flask, send_from_directory


app = Flask(__name__)
client = vision.ImageAnnotatorClient()
kgapi = build("kgsearch", "v1", developerKey=os.environ["KGSEARCH_API"])


@app.route("/<path:path>")
def send_img(path):
    return send_from_directory("", path)


def get_breeds():

    dog_image_name = "two-doggos.jpg"
    this_folder = Path(__file__).resolve().parent

    with io.open(dog_image_name, "rb") as image:
        content = image.read()

    image = vision.Image(content=content)
    objects = client.object_localization(image=image).localized_object_annotations

    im = Image.open(dog_image_name)

    count = 0
    output = []
    for obj in objects:
        count += 1

        # split image
        box = [
            (vertex.x * im.width, vertex.y * im.height)
            for vertex in obj.bounding_poly.normalized_vertices
        ]
        item = im.crop((box[0][0], box[0][1], box[2][0], box[2][1]))

        item_fn = this_folder.joinpath(f"doggo_{count}.png")
        item.save(item_fn)
        output.append(f"<img src='/{item_fn.name}' />")

        # detect labels on individual image
        with io.open(item_fn, "rb") as image:
            content = image.read()

        image = vision.Image(content=content)
        response = client.label_detection(image=image)

        labels = [label.description for label in response.label_annotations]
        mids = [label.mid for label in response.label_annotations]
        output.append(f"Doggo {count}")
        output.append(str(labels))

        # check MIDs
        response = kgapi.entities().search(ids=mids).execute()
        results = [resp["result"] for resp in response["itemListElement"]]
        breed = None
        for item in results:
            if "description" in item.keys() and item["description"] == "Dog breed":
                breed = item["name"]
                continue

        if breed:
            output.append(f"Breed: {breed}\n")
        else:
            output.append("Breed not detected in labels.\n")

    return "<br>".join(output)


@app.route("/")
def hello_doggo():
    result = get_breeds()

    return result


if __name__ == "__main__":
    app.run(host="localhost", port=8080, debug=True)
