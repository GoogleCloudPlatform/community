import io
from pprint import pprint
from google.cloud import vision

client = vision.ImageAnnotatorClient()

with io.open("doggo.jpg", "rb") as image:
    content = image.read()

image = vision.Image(content=content)

objects = client.object_localization(
        image=image).localized_object_annotations

pprint(objects)

for item in objects:
    print(item.name)

labels = client.label_detection(image=image)

pprint(labels)

print([label.description for label in labels.label_annotations])
