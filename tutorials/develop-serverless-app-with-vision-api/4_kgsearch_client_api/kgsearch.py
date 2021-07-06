import json
import os

from googleapiclient.discovery import build

# initialise the API with our developer key
kgapi = build("kgsearch", "v1", developerKey=os.environ["KGSEARCH_API"])

mids = ["/m/016wkx"]  # pug

# perform a search
response = kgapi.entities().search(ids=mids).execute()
print(json.dumps(response, indent=2))
