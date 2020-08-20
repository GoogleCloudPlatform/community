---
title: Using Node.js to Calculate the Size of a BigQuery Dataset
description: Learn how to use Node.js to calculate the size of a BigQuery dataset.
author: jmdobry
tags: BigQuery, Node.js
date_published: 2016-01-18
---
This tutorial shows how to use Node.js to calculate the size of a BigQuery
dataset.

We will create a small Node.js script that accepts a project ID and a dataset ID
and calculates the size of the dataset.

## Setup

1. Install [Node.js](https://nodejs.org/en/download/).
1. Create a file named `index.js`.
1. Install the `@google-cloud/bigquery` package from NPM:

        npm install @google-cloud/bigquery

## Validating input

The first step read and validate arguments that are passed to the script from
the command-line. Add the following to `index.js`:

[embedmd]:# (index.js /.*Read and validate.*/ /}/)
```js
// Read and validate the input arguments
const [projectId, datasetId] = process.argv.slice(2);

if (!projectId || !datasetId) {
  console.log('Usage: node index.js PROJECT_ID DATASET_ID');
  console.log('Example: node index.js bigquery-public-data hacker_news');
  process.exit();
}
```

This code ensure the a project ID and dataset ID are passed to the script.

## Instantiating a BigQuery client

The next step is to instantiate the BigQuery Node.js client. Add the following
to `index.js`:

[embedmd]:# (index.js /.*Instantiate.*/ /}\);/)
```js
// Instantiate a BigQuery client
const bigquery = require('@google-cloud/bigquery')({
  projectId: projectId
});
```

## Specifying the target dataset

With the client instantiated, we can now create a reference to the specified
dataset. Add the following to `index.js`:

[embedmd]:# (index.js /.*References.*/ /;/)
```js
// References an existing dataset, e.g. "my_dataset"
const dataset = bigquery.dataset(datasetId);
```

## Calculating the dataset size

Finally, we can load the dataset's table and sum their sizes. Add the following
to `index.js`:

[embedmd]:# (index.js /.*Lists.*/ /}\);/)
```js
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
```

## Run the script

Run the `index.js` script against BigQuery's public Hacker News dataset:

    node index.js bigquery-public-data hacker_news

## The complete code

Here is the complete source code:

[embedmd]:# (index.js)
```js
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
```

You can also view the source code and its tests [here](https://github.com/GoogleCloudPlatform/community/blob/master/tutorials/using-nodejs-to-calculate-the-size-of-a-bigquery-dataset);


You can check out [Node.js and Google Cloud Platform][nodejs-gcp] to get an
overview of Node.js and learn ways to run Node.js apps on Google Cloud Platform.

[nodejs-gcp]: running-nodejs-on-google-cloud
