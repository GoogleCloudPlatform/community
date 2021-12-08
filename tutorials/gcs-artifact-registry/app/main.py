import os
import json
import subprocess
import requests
import pandas as pd
import google.auth
import google.cloud.storage
import twine
from flask import Flask, request
from cloudevents.http import from_http

app = Flask(__name__)

PROJECT = os.environ.get('PROJECT')
BUCKET = os.environ.get('BUCKET')
REGION = os.environ.get('REGION', 'asia-southeast1')
REGISTRY_NAME = os.environ.get('REGISTRY_NAME', 'python-repo')
REGISTRY_API = (
                  f'https://artifactregistry.googleapis.com/v1beta2/projects/'
                  f'{PROJECT}/locations/{REGION}/repositories/{REGISTRY_NAME}/files'
                )
REGISTRY_PATH = f'https://{REGION}-python.pkg.dev/{PROJECT}/{REGISTRY_NAME}/'

  
@app.route("/", methods = ['POST'])
def trigger_gcs():
    # getting the credentials and project details for gcp project
    credentials, your_project_id = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])

    #getting request object
    auth_req = google.auth.transport.requests.Request()
    credentials.refresh(auth_req) #refresh token

    # create a CloudEvent
    event = from_http(request.headers, request.get_data())
    registry_list = ar_query(credentials)
    response = trigger_upload( event.data['name'], registry_list)
    print('\n'.join(response))
    return '<br/>'.join(response)

  
def ar_query(credentials):
    r = requests.get(REGISTRY_API, 
                 headers={'Authorization': 'Bearer ' + str(credentials.token)})
    if r.status_code == 200:
        if r.json() == {}:
            return []
        else: 
            #existing packges in artifact registry
            df=pd.DataFrame.from_records(r.json()['files'])
            df['packages'] =  df['name'].apply(lambda x: x.split('%2F')[-1])
            return df['packages'].values
    else:
        raise ValueError("Error Querying Artifact Registry")

        
def trigger_upload(package_name, item_list):
    client = google.cloud.storage.Client()
    output = []
    if package_name.split('/')[-1] == '':
        pass
    elif not package_name.endswith('.whl'):
        output.append('error: ' + package_name.split('/')[-1])
    elif package_name.split('/')[-1] in item_list:
        output.append('exist: ' + package_name.split('/')[-1])
    else:
        bucket = client.get_bucket(BUCKET)
        blob = bucket.blob(package_name)
        print('uploading ' + package_name.split('/')[-1])
        blob.download_to_filename('/tmp/' + package_name.split('/')[-1])
        subprocess.run(['twine', 'upload', '--repository-url', REGISTRY_PATH, '/tmp/' + package_name.split('/')[-1]], check=True)
        output.append('uploaded: ' + package_name.split('/')[-1])
    return output 
  
  
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
