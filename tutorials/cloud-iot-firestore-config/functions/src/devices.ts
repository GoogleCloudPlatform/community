const {google} = require('googleapis')
interface Credential {};

interface Device {
  id: string;
  name?: string;
  readonly numId?: string;
  credentials: Credential[];
  "config": any[];

  // many of the following fields could be added to the device interface:

  // "lastHeartbeatTime": string,
  // "lastEventTime": string,
  // "lastStateTime": string,
  // "lastConfigAckTime": string,
  // "lastConfigSendTime": string,
  // "blocked": boolean,
  // "lastErrorTime": string,
  // "lastErrorStatus": {
  //   object(Status)
  // },
  // {
  //   object(DeviceConfig)
  // },
  // "state": {
  //   object(DeviceState)
  // },
  // "metadata": {
  //   string: string,
  //   ...
  // },
}

export class DeviceManager {
  client: any;
  ready:Boolean = false;
  private parentName: string = '';
  private registryName: string = '';

  setClient(err: Error, hClient: any, project: string) {
    if (err) {
      console.error(err);
      return;
    }
    let aClient = hClient;
    const scopes = ['https://www.googleapis.com/auth/cloud-platform'];
    if (hClient.createScopedRequired && hClient.createScopedRequired()) {
      // Scopes can be specified either as an array or as a single, space-delimited string.
      aClient = hClient.createScoped(scopes);
    }
    this.client = google.cloudiot({
      version: 'v1',
      auth: aClient
    });
    this.parentName = `projects/${project}/locations/${this.region}`;
    this.registryName = `${this.parentName}/registries/${this.registryId}`
    this.ready = true;
  }

  constructor(private registryId:string, private region:string='us-central1') {
    google.auth.getApplicationDefault(this.setClient.bind(this))
  }
  
  createDevice(device:any) {
    return new Promise((resolve, reject) => {
      const request = {
        parent: this.registryName,
        resource: device
      }
      this.client.projects.locations.registries.devices.create(request, (err:any, data:any) => {
        if (err) {
          console.error(err);
          return reject(err);
        } else {
          // console.log('device created');
          resolve(data);
        }
      });
    });
  }

  updateDevice(deviceId:string, device:any, updateMask?:any) {
    return new Promise((resolve, reject) => {
      const request = {
        name:`${this.registryName}/devices/${deviceId}`,
        resource: device,
      }
      if (updateMask) {
        // tslint:disable-next-line: no-any
        (request as any)['updateMask'] = updateMask;
      }
      this.client.projects.locations.registries.devices.patch(request, (err:any, resp:any) => {
        if (err) {
          console.error(err);
          return reject(err);
        } else {
          resolve(resp.data);
        };
      }); 
    });
  }

  deleteDevice(deviceId:string) {
    return new Promise((resolve, reject) => {
      console.log("delete"); 
      this.client.projects.locations.registries.devices.delete({name:`${this.registryName}/devices/${deviceId}`}, (err:any, resp:any) => {
        if (err) {
          console.error(err);
          return reject(err);
        } else {
          resolve(resp.data);
        };
      }); 
    });
  }

  // sendConfig(deviceId:string, config) {}

  //getState(deviceId:string) {}

  getDevice(deviceId:string) {
    return new Promise((resolve, reject) => {
      this.client.projects.locations.registries.devices.get({name:`${this.registryName}/devices/${deviceId}`}, (err:any, resp:any) => {
        if (err) {
          console.error(err);
          return reject(err);
        } else {
          resolve(resp.data);
        };
      }); 
    });
  }

  listDevices(pageToken?:string) {
    return new Promise((resolve, reject) => {
      const request: any = {
        parent: this.registryName,
        //resource: body
        pageSize: 50,
      };
      if (pageToken) {
        request['pageToken'] = pageToken;
      }
      // console.log(request);
      // console.log(this.client);
      this.client.projects.locations.registries.devices.list(request, (err:any, resp:any) => {
        if (err) {
          console.error(err);
          return reject(err);
        } else {
          resolve(resp.data);
        };
      });
    });
  }

  updateConfig(deviceId:string, config:any) {
    return new Promise((resolve, reject) => {
      const request = {
        name:`${this.registryName}/devices/${deviceId}`,
        binaryData: Buffer.from(JSON.stringify(config)).toString("base64"),
      }
      this.client.projects.locations.registries.devices.modifyCloudToDeviceConfig(request, (err:any, resp:any) => {
        if (err) {
          console.error(err);
          return reject(err);
        } else {
          resolve(resp.data);
        };
      });
    });
  }

  updateConfigBinary(deviceId:string, config:Buffer) {
    return new Promise((resolve, reject) => {
      const request = {
        name:`${this.registryName}/devices/${deviceId}`,
        binaryData: config.toString("base64"),
      }
      this.client.projects.locations.registries.devices.modifyCloudToDeviceConfig(request, (err:any, resp:any) => {
        if (err) {
          console.error(err);
          return reject(err);
        } else {
          resolve(resp.data);
        };
      });
    });
  }

}