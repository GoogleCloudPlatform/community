import * as functions from 'firebase-functions';
const admin = require('firebase-admin');


import axios, {
  AxiosRequestConfig,
  AxiosResponse,
  AxiosError,
  AxiosInstance,
  AxiosAdapter,
  Cancel,
  CancelToken,
  CancelTokenSource,
  Canceler
} from 'axios';


import { DeviceManager } from './devices';
import { runInDebugContext } from 'vm';
// // Start writing Firebase Functions
// // https://firebase.google.com/docs/functions/typescript
//
// export const helloWorld = functions.https.onRequest((request, response) => {
//  response.send("Hello from Firebase!");
// });

admin.initializeApp({
  credential: admin.credential.applicationDefault()
});

// TODO trim trailing slash and space
const MENDER_URL = functions.config().mender.url;

// TODO not safe to assume one registry - but for caching for now
let dm = new DeviceManager('mender-demo');

// only for dev, for self signed certs on mender server
process.env.NODE_TLS_REJECT_UNAUTHORIZED = "0";

async function menderPreAuth(device: any) {
  let JWT: string = "";

  // TODO these need to be in env injection
  const authConfig: AxiosRequestConfig = {
    url: '/api/management/v1/useradm/auth/login',
    method: 'post',
    baseURL: `${MENDER_URL}/`,
    auth: {
      username: functions.config().mender.username,
      password: functions.config().mender.pw
    },
  };

  let auth: AxiosResponse = await axios(authConfig);
  JWT = auth.data;
  // console.log(JWT);

  const preauthConfig: AxiosRequestConfig = {
    url: '/api/management/v1/admission/devices',
    method: 'post',
    baseURL: `${MENDER_URL}/`,
    headers: {'Authorization': `Bearer ${JWT}`,
              'Content-Type': 'application/json',
      },
    data: {
      // device_identity: `{\"extra_identity_info\":\"${device.metadata.device_identifier}\",\"mac\":\"${device.metadata.mac_address}\"}`,
      // device_identity: `{\"extra_identity_info\":\"${device.metadata.device_identifier}\",\"mac\":\"${device.metadata.mac_address}\"}`,
      device_identity: `{\"google_iot_id\":\"${device.id}\"}`,
      // TODO, the use of newlines is very picky
      key: device.credentials[0].publicKey.key.trim() + "\n"
    },
  };
  try {
    let preauth: AxiosResponse = await axios(preauthConfig);
    return 'device created ok';
  }
  catch (e) {
    console.log('device creation error');
    console.error(e);
    throw(e);
  }
  
}

export const deviceEvent = functions.pubsub.topic('registration-events').onPublish(async (message) => {
  let audit = message.json;
  console.log(audit.protoPayload.methodName);
  switch (audit.protoPayload.methodName) {
    case 'google.cloud.iot.v1.DeviceManager.CreateDevice':
    case 'google.cloud.iot.v1.DeviceManager.UpdateDevice':
      await dm.setAuth();
      const deviceNumId = audit.resource.labels.device_num_id;
      const device = await dm.getDevice(deviceNumId);
      console.log(JSON.stringify(device));
      try {
        const authResult = await menderPreAuth(device);
        console.log(authResult);
        const configResult = await dm.updateConfig(deviceNumId, {mender_server: MENDER_URL});
        console.log(configResult);
      }
      catch (e) {
        console.log("error");
        console.error(e);
      };

    
    // TODO - delete not handled
    // case 'google.cloud.iot.v1.DeviceManager.DeleteDevice':
  };
  console.log("shouldn't be here");
  return true;
});
