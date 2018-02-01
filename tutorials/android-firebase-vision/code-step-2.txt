const Vision = require("@google-cloud/vision");
const functions = require('firebase-functions');
const admin = require('firebase-admin');

const vision = new Vision();
admin.initializeApp(functions.config().firebase);
const db = admin.firestore();

exports.callVision = functions.storage.object().onChange(event => {
    const object = event.data;
    const fileBucket = object.bucket;
    const filePath = object.name;
    const gcsPath = `gs://${fileBucket}/${filePath}`;
    const req = {
      source: {
        imageUri: gcsPath
      }
    };

    // Call the Vision API's web detection and safe search detection endpoints
    console.log(`doingrequest: ${req}`);
    return vision.labelDetection(req).then(response => {
        let labels = response[0].labelAnnotations;
        return {labels: labels};
    }).then((visionResp) => {
        let imageRef = db.collection('images').doc(filePath.slice(7));
        return imageRef.set(visionResp);
    })
    .catch(err => {
        console.log('vision api error', err);
    });
});
