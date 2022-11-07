import ee
import os

# Initialize the Earth Engine API
ee.Initialize()

# Retrieve the environment variable of the Cloud Storage bucket for storing images
bucket_name = os.environ['IMAGES_BUCKET']

# Specify a region in the US (roughly the state of Colorado) to reduce the export time for the sake of example
colorado = ee.Geometry.Rectangle([-104, 37, -102, 38]);

# Select the first (and only) image from the Cropland image collection for the year 2019, and the cropland band, which gives us the crop type. Currently, Geobeam will only ingest a single band from a GeoTIFF at time.
image = ee.ImageCollection('USDA/NASS/CDL').filter(ee.Filter.date('2019-01-01', '2019-01-02')).first();
cropland = image.select('cropland');
task_config = {
    'description': 'cropland',
    'crs': 'EPSG:4326',  # specify this projection to ensure Biquery can ingest it properly
    'scale': 30, # also necessary to specify scale when reprojecting (30m is the original dataset scale)
    'bucket': bucket_name,
    'fileNamePrefix': 'croplandExport',
    'region': colorado,
    'maxPixels': 1e12 #increase max pixels limit for exports 
}

task = ee.batch.Export.image.toCloudStorage(cropland, **task_config)
task.start()
print('Please wait for 5 minutes for the export to GCS to complete')

