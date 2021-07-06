import io
from pathlib import Path

from google.cloud import vision
from PIL import Image, ImageDraw


# initialise the Vision API
client = vision.ImageAnnotatorClient()

# load the sample image
dog_image_name = "two-doggos.jpg"

with io.open(dog_image_name, "rb") as image:
    content = image.read()

image = vision.Image(content=content)

# perform object detection
objects = client.object_localization(image=image).localized_object_annotations

im = Image.open(dog_image_name)
draw = ImageDraw.Draw(im)

for obj in objects:
    # draw lines between all the points identified
    box = [
        (vertex.x * im.width, vertex.y * im.height)
        for vertex in obj.bounding_poly.normalized_vertices
    ]
    draw.line(box + [box[0]], width=5, fill="#4285F4")

# save the image into the directory that holds this file
im.save(Path(__file__).resolve().parent.joinpath("result.png"))
