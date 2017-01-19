'use strict';

const assert = require('assert');
const utils = require('../../test/utils');

const cmd = 'node .';
const cwd = __dirname;

const usage = 'Usage: node index.js PROJECT_ID DATASET_ID';
const example = 'Example: node index.js bigquery-public-data hacker_news';

it('should validate args', () => {
  return utils.runAsync(`${cmd}`, cwd)
    .then((output) => {
      assert(output.includes(usage));
      assert(output.includes(example));

      return utils.runAsync(`${cmd} bigquery-public-data`, cwd);
    })
    .then((output) => {
      assert(output.includes(usage));
      assert(output.includes(example));
    });
});

if (process.env.GCLOUD_PROJECT && process.env.GOOGLE_APPLICATION_CREDENTIALS) {
  it('should calculate the size of a dataset', () => {
    return utils.runAsync(`${cmd} bigquery-public-data hacker_news`, cwd)
      .then((output) => {
        assert(output.includes(`Size of hacker_news`));
        assert(output.includes(`MB`));
      });
  });
} else {
  console.log(`Skipping test in ${__dirname}`);
  console.log('Set GCLOUD_PROJECT and GOOGLE_APPLICATION_CREDENTIALs env vars to run this test.');
}
