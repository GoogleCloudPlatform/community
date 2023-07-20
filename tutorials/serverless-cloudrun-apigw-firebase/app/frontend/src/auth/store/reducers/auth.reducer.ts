import { createReducer, on } from '@ngrx/store';
import { Employee } from "../../../interfaces/employee.interface";
import * as AuthActions from '../actions/auth.actions';

export interface LoginState {
  employee: Employee;
  loaded: boolean;
  loading: boolean;
  error: any;
  authenticated: boolean;
}

export const initialState: LoginState = {
  employee: {},
  loaded: false,
  loading: false,
  error: null,
  authenticated: false
};

export const reducer = createReducer(
  initialState,
  on(AuthActions.login, state => ({
    ...state,
    loaded: false,
    loading: true,
    error: null,
    authenticated: false
    })
  ),
  on(AuthActions.loginSuccess, state => ({
    ...state,
    loaded: true,
    loading: false,
    error: null,
    authenticated: false
    })
  ),
  on(AuthActions.loginFail, (state, { errors }) => ({
    ...state,
    loaded: false,
    loading: false,
    error: errors,
    authenticated: false
    })
  ),
  on(AuthActions.googleLogin, state => ({
    ...state,
    loaded: false,
    loading: true,
    error: null,
    authenticated: false
    })
  ),
  on(AuthActions.googleLoginSuccess, state => ({
      ...state,
      loaded: true,
      loading: false,
      error: null,
      authenticated: false
  })
  ),
  on(AuthActions.googleLoginFail, (state, { errors }) => ({
      ...state,
      loaded: false,
      loading: false,
      error: errors,
      authenticated: false
  })
  ),
  on(AuthActions.register, state => ({
    ...state,
    loaded: false,
    loading: true,
    error: null,
    authenticated: false
    })
  ),
  on(AuthActions.registerSuccess, state => ({
    ...state,
    loaded: true,
    loading: false,
    error: null,
    authenticated: false
    })
  ),
  on(AuthActions.registerFail, (state, { errors }) => ({
    ...state,
    loaded: false,
    loading: false,
    error: errors,
    authenticated: false
    })
  ),
  on(AuthActions.logout, state => ({
    ...state,
    loaded: false,
    loading: true,
    error: null,
    authenticated: false
    })
  ),
  on(AuthActions.logoutSuccess, state => ({
    ...state,
    loaded: true,
    loading: false,
    error: null,
    authenticated: false
    })
  ),
  on(AuthActions.logoutFail, (state, { errors }) => ({
    ...state,
    loaded: false,
    loading: false,
    error: errors,
    authenticated: false
    })
  ),
  on(AuthActions.authenticated, (state, { employee }) => ( {
    ...state,
    employee,
    loaded: true,
    loading: false,
    error: null,
    authenticated: true
  })),
  on(AuthActions.notAuthenticated, state => ({
    ...state,
    employee: {},
    loaded: false,
    loading: false,
    error: null,
    authenticated: false
  })),
  on(AuthActions.forgotPassword, state => ({
    ...state,
    employee: {},
    loaded: false,
    loading: false,
    error: null,
    authenticated: false
  })),
  on(AuthActions.forgotPasswordSuccess, state => ({
    ...state,
    loaded: true,
    loading: false,
    error: null,
    authenticated: false
    })
  ),
  on(AuthActions.forgotPasswordFail, (state, { errors }) => ({
    ...state,
    loaded: false,
    loading: false,
    error: errors,
    authenticated: false
    })
  ),
);

export const getAuthEmployee = (state: LoginState) => state.employee;
export const getLoadedAuthEmployee = (state: LoginState) => state.loaded;
export const getLoadingAuthEmployee = (state: LoginState) => state.loading;
export const getAuthError = (state: LoginState) => state.error;
