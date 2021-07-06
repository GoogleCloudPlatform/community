import io
from pprint import pprint

from google.cloud import vision

# initialise object within the API
client = vision.ImageAnnotatorClient()

with io.open("doggo.jpg", "rb") as image:
    content = image.read()

image = vision.Image(content=content)

# perform localisation
objects = client.object_localization(image=image).localized_object_annotations

pprint(objects)

for item in objects:
    print(item.name)

# perform label detection
labels = client.label_detection(image=image)

pprint(labels)

print([label.description for label in labels.label_annotations])
