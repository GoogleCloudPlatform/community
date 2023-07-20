import { ActionReducerMap, createFeatureSelector } from '@ngrx/store';
import { RouterStateUrl } from './router.reducer';
import * as fromRouter from '@ngrx/router-store';
// import * as fromEmployees from './employee.reducer';

export interface AppState {
  routerState: fromRouter.RouterReducerState<RouterStateUrl>;
  // employeesState: fromEmployees.State;
}

// Registering reducers with the AuthState
export const reducers: ActionReducerMap<AppState> = {
  routerState: fromRouter.routerReducer,
  // employeesState: fromEmployees.reducer,
};

// create the main feature selector
export const getAppState = createFeatureSelector<AppState>('appRoot');
