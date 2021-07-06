import os
import json
from googleapiclient.discovery import build
 
kgapi = build("kgsearch", "v1", developerKey=os.environ["KGSEARCH_API"])

mids = ["/m/016wkx"] # pug

response = kgapi.entities().search(ids=mids).execute()
print(json.dumps(response, indent=2))
