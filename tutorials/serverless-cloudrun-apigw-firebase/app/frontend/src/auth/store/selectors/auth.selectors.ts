import { createSelector } from '@ngrx/store';

import * as fromFeature from '../reducers';
import * as fromAuth from '../reducers/auth.reducer';

export const selectAuthState = createSelector(fromFeature.getAuthState, (state: fromFeature.AuthState) => state.auth);

export const getAuthenticationEmployee = createSelector(selectAuthState, fromAuth.getAuthEmployee);
export const getAuthenticationLoading = createSelector(selectAuthState, fromAuth.getLoadingAuthEmployee);
export const getAuthenticationLoaded = createSelector(selectAuthState, fromAuth.getLoadedAuthEmployee);
export const getAuthenticationErrors = createSelector(selectAuthState, fromAuth.getAuthError);
