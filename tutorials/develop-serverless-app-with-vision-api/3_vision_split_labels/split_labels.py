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


count = 0
for obj in objects:
    count += 1
    box = [
        (vertex.x * im.width, vertex.y * im.height)
        for vertex in obj.bounding_poly.normalized_vertices
    ]

    # crop the subimage, save it to disk
    item = im.crop((box[0][0], box[0][1], box[2][0], box[2][1]))
    item_fn = this_folder.joinpath(f"doggo_{count}.png")
    item.save(item_fn)

    # open the new image and process it
    with io.open(item_fn, "rb") as image:
        content = image.read()

    image = vision.Image(content=content)
    response = client.label_detection(image=image)

    print(item_fn.name)
    print([label.description for label in response.label_annotations])
