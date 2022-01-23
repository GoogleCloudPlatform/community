import { DeviceManager } from './devices';


let dm = new DeviceManager('t-registry');

let dostuff = function () {
  // dm.listDevices().then(data => {
  //   console.log(data);
  // });
  // dm.getDevice('d-1d8cb6d8-5d03-4f5c-ac92-c15d4f32b6f5').then(data => {
  //   console.log(data);
  // });
  let newD = {blocked: true}

  // dm.updateDevice('d-014f3f0d-5bbd-4efa-b389-4a7a7824cbf4', newD, 'blocked').then(data => {
  dm.updateDevice('d-014f3f0d-5bbd-4efa-b389-4a7a7824cbf4', newD).then(data => {
    console.log(data);
  })
  // console.log('result');
  // console.log(x);
  setTimeout(() => console.log('done'), 2000);
}

setTimeout(() => dostuff(), 2000);
