import { ActionReducerMap, createFeatureSelector } from '@ngrx/store';
import * as fromEmployees from './employee.reducer';

export interface EmployeeState {
  employeesState: fromEmployees.State;
}

// Registering reducers with the AuthState
export const reducers: ActionReducerMap<EmployeeState> = {
  employeesState: fromEmployees.reducer
};

// create the main feature selector
export const getAppState = createFeatureSelector<EmployeeState>('EmployeeState');
