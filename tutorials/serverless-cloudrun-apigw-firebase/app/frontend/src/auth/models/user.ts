export interface User {
  email: string;
  uid: string;
  displayName: string;
  authenticated: boolean;
}

export interface UserCredentials {
  email: string;
  password: string;
}
