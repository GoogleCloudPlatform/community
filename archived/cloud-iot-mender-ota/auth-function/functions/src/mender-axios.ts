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

// https://github.com/axios/axios/blob/master/test/typescript/axios.ts

let JWT: string = "";

const authConfig: AxiosRequestConfig = {
  url: '/api/management/v1/useradm/auth/login',
  method: 'post',
  baseURL: 'https://35.193.149.58/',
  auth: {
    username: 'mender@example.com',
    password: 'Mender@2017'
  },
};

// this is taken directly from a current working function example
const devicearg = {"id":"menderpi","name":"projects/iot-provisioning/locations/us-central1/registries/mender-demo/devices/2662516839362241","numId":"2662516839362241","credentials":[{"publicKey":{"format":"RSA_PEM","key":"-----BEGIN PUBLIC KEY-----\nMIIBojANBgkqhkiG9w0BAQEFAAOCAY8AMIIBigKCAYEAzJf/lGniFwenACaq6Uwc\nE/j1z5oGy6ukwbV8e27ELb/s4byG1XOyO8Ai21Vm1vDsNVF1PGldlmoX5tPDysrS\nq8U0l3zg7FH2eRqz4M9oYzkzHPN+zty5KgngmeMQ/pGD3jv2S330BugtpGqwzfCi\nJBjSMgl4DqRubZp7nl2U4iVdAeXvkhJTTEpZ3Bhr9R4+oKkW8nbB/g4xvWsIbCGu\n4h2MeYyLwhPQNoBjBCQR/Ncbn++7RFRfgyqPbqHIxYEdn6DDoQblkm6WvvQx6hUm\n4JOoiHLQEj9qYljpUkU9EKuud16Ml4l6B2XaklOP16i13dIngeLmLAm6pXxfw1/j\nEPs1dZC4QtdkMwB4ozk+QGzIjIKEi8Jh8QU1/MifWQkRdA2DaA6pgEqi/HYzczHW\nlezp4E31Tjm/BNlo7hSF/ISmweKun6mj3mIleLLeHN3sqbvQnz+tKPDVukCVWIY1\nQZlhVGYRR1KyZPvqLNlmUAh8VXPV8frVam9PjFXI18ePAgMBAAE=\n-----END PUBLIC KEY-----"},"expirationTime":"1970-01-01T00:00:00Z"}],"config":{"version":"1","cloudUpdateTime":"2018-05-10T03:50:18.301714Z"},"metadata":{"mendermac":"b8:27:eb:c5:b1:04","dummy":"fff"}};

// console.log(device);


process.env.NODE_TLS_REJECT_UNAUTHORIZED = "0";

async function callMenderApi(device: any) {
  let auth: AxiosResponse = await axios(authConfig);
  JWT = auth.data;
  // console.log(JWT);

  const preauthConfig: AxiosRequestConfig = {
    url: '/api/management/v1/admission/devices',
    method: 'post',
    baseURL: 'https://35.193.149.58/',
    headers: {'Authorization': `Bearer ${JWT}`,
              'Content-Type': 'application/json',
      },
    data: {
      device_identity: `{\"mac\":\"${device.metadata.mendermac}\"}`,
      key: device.credentials[0].publicKey.key + "\n"
    },
  };
  // console.log(preauthConfig);
  try {
    let preauth: AxiosResponse = await axios(preauthConfig);
  }
  catch (e) {
    console.log("error");
    console.error(e);
  }
  return 'ok';
}

callMenderApi(devicearg).then((result) => console.log(result)).catch(e => console.error(e));
