/*
 Very simple authenticated asset proxy
 WEB  =>  IAP =>  APP Engine  =>  Cloud Storage
*/

const { Storage } = require('@google-cloud/storage');
const storage = new Storage();
const mime = require('mime/lite');
const express = require('express');
const app = express();

const PORT = process.env.PORT || 8080;
app.listen(PORT, () => {
  console.log(`App listening on port ${PORT}`);
});

app.get('*', (req, res) => {
  const fileName = req.originalUrl.substring(1);
  const fileExt = fileName.match(/\.([^.]+)$/);
  if (!fileExt || !fileExt[1] || !fileName) {
    res.status(400).send('<h1>400 Bad request.</h1>').end();
    return;
  }
  const fileMime = mime.getType(fileExt[1]);
  const bucketName = process.env.GCS_BUCKET || 'tw-aaa-assets';
  const bucket = storage.bucket(bucketName);
  const file = bucket.file(fileName);
  file.download(function (err, contents) {
    if (err) {
      res.status(404).send('<h1>404 File not found.</h1>').end();
    } else {
      res.setHeader('Content-Type', fileMime);
      res.setHeader('Content-Disposition', 'inline');
      res.status(200).send(contents).end();
    }
  });
});
