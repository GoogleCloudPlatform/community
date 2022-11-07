'use strict';

const Firestore = require('@google-cloud/firestore');

const PROJECTID = '[REPLACE-WITH-YOUR-PROJECT-ID]';
const COLLECTION_NAME = 'cloud-functions-firestore';

const firestore = new Firestore({
  projectId: PROJECTID,
  timestampsInSnapshots: true
  // NOTE don't hardcode your project credentials here.
  // If you have to, export the following to your shell:
  //   GOOGLE_APPLICATION_CREDENTIALS=<path>
  // keyFilename: '/cred/cloud-functions-firestore-000000000000.json',
});

/**
 * Retrieve or Store a method into Firestore
 *
 * Responds to any HTTP request.
 *
 * GET = retrieve
 * POST = store (no update)
 *
 * success: returns the document content in JSON format & status=200
 *    else: returns an error:<string> & status=404
 *
 * @param {!express:Request} req HTTP request context.
 * @param {!express:Response} res HTTP response context.
 */
exports.main = (req, res) => {
  if (req.method === 'POST') {
    // store/insert a new document
    const data = (req.body) || {};
    const ttl = Number.parseInt(data.ttl);
    const ciphertext = (data.ciphertext || '')
      .replace(/[^a-zA-Z0-9\-_!.,; ']*/g, '')
      .trim();
    const created = new Date().getTime();

    // .add() will automatically assign an id
    return firestore.collection(COLLECTION_NAME).add({
      created,
      ttl,
      ciphertext
    }).then(doc => {
      console.info('stored new doc id#', doc.id);
      return res.status(200).send(doc);
    }).catch(err => {
      console.error(err);
      return res.status(404).send({
        error: 'unable to store',
        err
      });
    });
  }

  // everything below this requires an id
  if (!(req.query && req.query.id)) {
    return res.status(404).send({
      error: 'No Id'
    });
  }
  const id = req.query.id.replace(/[^a-zA-Z0-9]/g, '').trim();
  if (!(id && id.length)) {
    return res.status(404).send({
      error: 'Empty Id'
    });
  }

  if (req.method === 'DELETE') {
    // delete an existing document by id
    return firestore.collection(COLLECTION_NAME)
      .doc(id)
      .delete()
      .then(() => {
        return res.status(200).send({ status: 'ok' });
      }).catch(err => {
        console.error(err);
        return res.status(404).send({
          error: 'unable to delete',
          err
        });
      });
  }

  // read/retrieve an existing document by id
  return firestore.collection(COLLECTION_NAME)
    .doc(id)
    .get()
    .then(doc => {
      if (!(doc && doc.exists)) {
        return res.status(404).send({
          error: 'Unable to find the document'
        });
      }
      const data = doc.data();
      if (!data) {
        return res.status(404).send({
          error: 'Found document is empty'
        });
      }
      return res.status(200).send(data);
    }).catch(err => {
      console.error(err);
      return res.status(404).send({
        error: 'Unable to retrieve the document',
        err
      });
    });
};
