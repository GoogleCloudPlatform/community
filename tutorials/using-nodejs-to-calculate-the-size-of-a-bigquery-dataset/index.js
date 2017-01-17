'use strict';

// Read and validate the input arguments
const [projectId, datasetId] = process.argv.slice(2);

if (!projectId || !datasetId) {
  console.log('Usage: node index.js PROJECT_ID DATASET_ID');
  console.log('Example: node index.js bigquery-public-data hacker_news');
  process.exit();
}

// Instantiate a BigQuery client
const bigquery = require('@google-cloud/bigquery')({
  projectId: projectId
});

// References an existing dataset, e.g. "my_dataset"
const dataset = bigquery.dataset(datasetId);

// Lists all tables in the dataset
dataset.getTables()
  .then((results) => results[0])
  // Retrieve the metadata for each table
  .then((tables) => Promise.all(tables.map((table) => table.get())))
  .then((results) => results.map((result) => result[0]))
  // Select the size of each table
  .then((tables) => tables.map((table) => (parseInt(table.metadata.numBytes, 10) / 1000) / 1000))
  // Sum up the sizes
  .then((sizes) => sizes.reduce((cur, prev) => cur + prev, 0))
  // Print and return the size
  .then((sum) => {
    console.log(`Size of ${dataset.id}: ${sum} MB`);
  });
