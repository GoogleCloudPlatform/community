import io
from pathlib import Path

from google.cloud import vision
from PIL import Image, ImageDraw

dog_image_name = "two-doggos.jpg"
this_folder = Path(__file__).resolve().parent

client = vision.ImageAnnotatorClient()
with io.open(dog_image_name, "rb") as image:
    content = image.read()

image = vision.Image(content=content)
objects = client.object_localization(image=image).localized_object_annotations

im = Image.open(dog_image_name)
draw = ImageDraw.Draw(im)

for obj in objects:
    box = [
        (vertex.x * im.width, vertex.y * im.height)
        for vertex in obj.bounding_poly.normalized_vertices
    ]
    draw.line(box + [box[0]], width=5, fill="#4285F4")

im.save(this_folder.joinpath("result.png"))
