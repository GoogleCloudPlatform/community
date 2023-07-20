import { ActionReducerMap, createFeatureSelector } from '@ngrx/store';
import * as fromAuth from './auth.reducer';

export interface AuthState {
  auth: fromAuth.LoginState
}

// registering reducers with the AuthState
export const reducers: ActionReducerMap<AuthState> = {
  auth: fromAuth.reducer
};

// create the main selector
export const getAuthState = createFeatureSelector<AuthState>('AuthState');
