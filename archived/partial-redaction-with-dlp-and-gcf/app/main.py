
"""Partially redact an image file containing credit card numbers and upload it to a
   Google Cloud Storage bucket. The script redacts the second and third set of digits
   of the credit card number

"""

import sys
import matplotlib
matplotlib.use('Agg')
import os
import json
from google.cloud import storage
import google.cloud.dlp

# Import libraries for image manipulation 
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
import matplotlib.patches as patches


# Set project_id
project_id = os.environ['GCP_PROJECT']

# Load configuration definitions
with open('config.json') as f:
    data = f.read()
config = json.loads(data)

def inspect_file(project, filename, info_types, min_likelihood=None,
                 max_findings=None, include_quote=True, mime_type=None):

    """Call Data Loss Prevention API to analyze a file for protected data.
    Args:
        project: The GCP project id to use as a parent resource.
        filename: The path to the file to inspect.
        info_types: A list of strings representing info types to look for.
            A full list of info type categories can be fetched from the API.
        min_likelihood: A string representing the minimum likelihood threshold
            that constitutes a match. One of: 'LIKELIHOOD_UNSPECIFIED',
            'VERY_UNLIKELY', 'UNLIKELY', 'POSSIBLE', 'LIKELY', 'VERY_LIKELY'.
        max_findings: The maximum number of findings to report; 0 = no maximum.
        include_quote: Boolean for whether to display a quote of the detected
            information in the results.
        mime_type: The MIME type of the file. If not specified, the type is
            inferred via the Python standard library's mimetypes module.
    Returns:
        None; the response from the API is printed to the terminal.
    """

    import mimetypes

    # Instantiate a client.
    dlp = google.cloud.dlp.DlpServiceClient()

    # Prepare info_types by converting the list of strings into a list of
    # dictionaries (protos are also accepted).
    if not info_types:
        info_types = ['FIRST_NAME', 'LAST_NAME', 'EMAIL_ADDRESS']
    info_types = [{'name': info_type} for info_type in info_types]

    # Construct the configuration dictionary. Keys which are None may
    # optionally be omitted entirely.
    inspect_config = {
        'info_types': info_types,
        'min_likelihood': min_likelihood,
        'limits': {'max_findings_per_request': max_findings},
    }

    # If mime_type is not specified, guess it from the filename.
    if mime_type is None:
        mime_guess = mimetypes.MimeTypes().guess_type(filename)
        mime_type = mime_guess[0]

    # Select the content type index from the list of supported types.
    supported_content_types = {
        None: 0,  # "Unspecified"
        'image/jpeg': 1,
        'image/bmp': 2,
        'image/png': 3,
        'image/svg': 4,
        'text/plain': 5,
    }
    content_type_index = supported_content_types.get(mime_type, 1)

    # Construct the item, containing the file's byte data.
    with open(filename, mode='rb') as f:
        item = {'byte_item': {'type': content_type_index, 'data': f.read()}}

    # Convert the project id into a full resource id.
    parent = dlp.project_path(project)

    # Call the API.
    response = dlp.inspect_content(parent, inspect_config, item)

    # Print out the results.
    if response.result.findings:
        for finding in response.result.findings:
            try:
                print('Quote: {}'.format(finding.quote))
            except AttributeError:
                pass
            print('Info type: {}'.format(finding.info_type.name))
            print('Likelihood: {}'.format(finding.likelihood))

            boxes = finding.location.content_locations[0].image_location.bounding_boxes

            for box in boxes:
            	#print('box: {}'.format(box))
            	pass

            return boxes

    else:
        print('No findings.')

def add_rectangles(orig_file_name, boxes, new_file_name):

    """Cover the digits delimited by the element in the 'boxes' array and save the file
    Args:
        orig_file_name: image file to edit
        boxes: array of boxes element containing the coordinates around the digits
        new_file_name: name under which the image file will be saved
    """

    im = np.array(Image.open(orig_file_name), dtype=np.uint8)
    
    # Create figure and axes
    fig,ax = plt.subplots(1)
    
    # Display the image
    ax.imshow(im)
    
    # Redact second and third set of credit card digits
    for box in [boxes[1], boxes[2]]:
    	# Create a Rectangle patch
    	rect = patches.Rectangle((box.left, box.top), box.width, box.height, linewidth=1, edgecolor='r',facecolor='black')
    
    	# Add the patch to the Axes
    	ax.add_patch(rect)
    
    #plt.show()
    plt.savefig(new_file_name)

def upload_and_delete(project, bucket, orig_file_name, temp_file_name):

    """Upload the file to a bucket and delete it from disk	
    Args:
        project: GCP project id
        bucket: GCP bucket id
        orig_file_name: name that the file will take when uploaded
        temp_file_name: name of the file in disk to be uploaded
    """
    
    client = storage.Client(project=project)
    bucket = client.get_bucket(bucket)
    blob = bucket.blob(orig_file_name)
    blob.upload_from_filename(temp_file_name)
    print('file {} uploaded'.format(orig_file_name))
    
    if os.path.exists(temp_file_name):
        os.remove(temp_file_name)

def download_file(project, bucket, orig_file_name, temp_file_name):

    """Download a file stored in a Google Cloud Storage bucket to the disk"""

    client = storage.Client(project=project)
    bucket = client.get_bucket(bucket)
    blob = bucket.blob(orig_file_name)
    blob.download_to_filename(temp_file_name)
    print('file {} downloaded'.format(orig_file_name))
    
def partial_dlp(data, context):
    
    """Execute the methods to detect boxes candidate for redaction, add rectangles to the image, 
       and upload them to the Google Cloud Storage bucket. Delete temp image after upload:
    """

    origin_bucket = data['bucket'] 
    origin_file_name = data['name']
    redacted_bucket = config['REDACTED_BUCKET'] 
    not_redacted_bucket = config['NOT_REDACTED_BUCKET']

    # Identify file extension and create temporary local file name
    _, file_ext = os.path.splitext(origin_file_name) 
    temp_file_name = '/tmp/temp_file_name{}'.format(file_ext)

    # Download to local file
    download_file(project_id, origin_bucket, origin_file_name, temp_file_name)

    # Run dlp api
    boxes = inspect_file(project_id, temp_file_name, ['CREDIT_CARD_NUMBER'],'VERY_UNLIKELY',0,True)

    # If there is redactable content found, redact the file and upload it to
    # the bucket for redacted files and delete local file
    if boxes:
    	add_rectangles(temp_file_name, boxes, temp_file_name)
    	upload_and_delete(project_id, redacted_bucket, origin_file_name, temp_file_name)

    # if there is *no* redactable content found, upload it to
    # bucket for not redacted files and delete local files
    else:
        upload_and_delete(project_id, not_redacted_bucket, origin_file_name, temp_file_name)
