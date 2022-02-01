import ee
import os

# Initialize the Earth Engine API
ee.Initialize()

# Retrieve the environment variable of GCS bucket for storing images
bucket_name = os.environ['IMAGES_BUCKET']

image = ee.ImageCollection("COPERNICUS/S2").first().select(['B4', 'B3', 'B2']);
task_config = {
    'description': 'copernicus-3',    
    'scale': 30,
    'bucket': bucket_name,
    'fileNamePrefix': 'copernicusExport'
}
task = ee.batch.Export.image.toCloudStorage(image, **task_config)
task.start()
print('Please wait for 5 minutes for the export to GCS to complete')
