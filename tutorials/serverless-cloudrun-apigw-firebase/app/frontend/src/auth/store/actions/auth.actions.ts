import { createAction, props } from '@ngrx/store';
import { Employee, EmployeeCredentials } from "../../../interfaces/employee.interface";


export const login = createAction('[Auth] Login', props<{ payload: EmployeeCredentials }>());
export const loginSuccess = createAction('[Auth] Login SUCCESS');
export const loginFail = createAction('[Auth] Login FAIL', props<{ errors: any }>());

export const register = createAction('[Auth] Register', props<{ payload: EmployeeCredentials }>());
export const registerSuccess = createAction('[Auth] Register SUCCESS');
export const registerFail = createAction('[Auth] Register FAIL', props<{ errors: any }>());

export const googleLogin = createAction('[Auth] Google Login');
export const googleLoginSuccess = createAction('[Auth] Google Login SUCCESS');
export const googleLoginFail = createAction('[Auth] Google Login FAIL', props<{ errors: any }>());

export const logout = createAction('[Auth] Logout');
export const logoutSuccess = createAction('[Auth] Logout SUCCESS');
export const logoutFail = createAction('[Auth] Logout FAIL', props<{ errors: any }>());

export const authenticated = createAction('[Auth] Authenticated', props<{ employee: Employee }>());
export const notAuthenticated = createAction('[Auth] Not Authenticated!!!');

export const forgotPassword = createAction('[Auth] Forgot Password', props<{ payload: { email: string } }>());
export const forgotPasswordSuccess = createAction('[Auth] Forgot Password Success');
export const forgotPasswordFail = createAction('[Auth] Forgot Password Fail ', props<{ errors: any }>());
