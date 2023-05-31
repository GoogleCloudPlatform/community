// function code taken from https://stackoverflow.com/questions/49111829/using-cloud-function-to-load-data-into-big-query-table-it-is-appending-to-the-t
// fixed by tfrantzen@google.com
exports.ToBigQuery_Stage = (event, callback) => {
  console.log(JSON.stringify(event.data));
  const file = event.data;

  const BigQuery = require('@google-cloud/bigquery');
  const Storage = require('@google-cloud/storage');

  // specify projectID and bigquery datasetID below
  const projectId = 'mikekahn-sandbox';
  const datasetId = 'avroimport';
  const bucketName = file.bucket;
  const filename = file.name;

  // Do not use the ftp_files Bucket to ensure that the bucket does not get crowded.
  // Change bucket to gas_ddr_files_staging
  // Set the table name (TableId) to the full file name including date,
  // this will give each table a new distinct name and we can keep a record of all of the files received.
  // This may not be the best way to do this... at some point we will need to archive and delete prior records.
  const dashOffset = filename.indexOf('-');
  const tableId = filename.substring(0, dashOffset) + '_STAGE';

  console.log(`Load ${filename} into ${tableId}.`);

  // Instantiates clients
  const bigquery = new BigQuery({
    projectId: projectId
  });

  const storage = Storage({
    projectId: projectId
  });

  // const metadata = {
  //   allowJaggedRows: true,
  //   skipLeadingRows: 1
  // };

  let job;

  // Loads data from a Google Cloud Storage file into the table
  bigquery
    .dataset(datasetId)
    .table(tableId)
    .load(storage.bucket(bucketName).file(filename))
    .then(results => {
      job = results[0];
      console.log(`Job ${job.id} started.`);

      // Wait for the job to finish
      return job;
    })
    .then(metadata => {
      // Check the job's status for errors
      const errors = metadata.status.errors;
      if (errors && errors.length > 0) {
        throw errors;
      }
    })
    .then(() => {
      console.log(`Job ${job.id} completed.`);
    })
    .catch(err => {
      console.error('ERROR:', err);
    });

  callback();
};
