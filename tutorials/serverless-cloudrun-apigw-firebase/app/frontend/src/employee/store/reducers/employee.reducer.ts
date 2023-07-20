import { createReducer, on } from '@ngrx/store';
import { EntityState, EntityAdapter, createEntityAdapter } from '@ngrx/entity';
import { Employee } from 'src/interfaces/employee.interface';
import * as EmployeeActions from '../actions/employee.actions';

export const employeesFeatureKey = 'employees';

export interface State extends EntityState<Employee> {
  // additional entities state properties
  selectedEmployeeId: string | null;
  loaded: boolean;
  loading: boolean;
  error: any;
}

export const adapter: EntityAdapter<Employee> = createEntityAdapter<Employee>();

export const initialState: State = adapter.getInitialState({
  // additional entity state properties
  selectedEmployeeId: null,
  loaded: false,
  loading: false,
  error: null
});


export const reducer = createReducer(
  initialState,
  on(EmployeeActions.addEmployee,
    (state, action) => adapter.addOne(action.employee, {
      ...state,
      loaded: false,
      loading: true,
      error: null
    })
  ),
  on(EmployeeActions.addEmployeeSuccess, state => ({
    ...state,
    loaded: true,
    loading: false,
    error: null
    })
  ),
  on(EmployeeActions.addEmployeeFail,
    (state, { errors }) => ({
      ...state,
      loaded: false,
      loading: false,
      error: errors
    })
  ),
  on(EmployeeActions.upsertEmployee,
    (state, action) => adapter.upsertOne(action.employee, state)
  ),
  on(EmployeeActions.addEmployees,
    (state, action) => adapter.addMany(action.employees, state)
  ),
  on(EmployeeActions.upsertEmployees,
    (state, action) => adapter.upsertMany(action.employees, state)
  ),
  on(EmployeeActions.updateEmployee,
    (state, action) => adapter.updateOne(action.employee, state)
  ),
  on(EmployeeActions.updateEmployees,
    (state, action) => adapter.updateMany(action.employees, state)
  ),
  on(EmployeeActions.deleteEmployee,
    (state, action) => adapter.removeOne(action.id, {
      ...state,
      loaded: false,
      loading: true,
      error: null
    })
  ),
  on(EmployeeActions.deleteEmployeeSuccess, state => ({
    ...state,
    loaded: true,
    loading: false,
    error: null
    })
  ),
  on(EmployeeActions.deleteEmployeeFail, (state, { errors }) => ({
    ...state,
    error: errors,
    loaded: false,
    loading: false,
  })),
  on(EmployeeActions.deleteEmployees,
    (state, action) => adapter.removeMany(action.ids, state)
  ),
  on(EmployeeActions.loadEmployees, state => ({
    ...state,
    loaded: false,
    loading: true
  })),
  on(EmployeeActions.loadEmployeesSuccess,
    (state, action) => adapter.setAll(action.employees, {
      ...state,
      loaded: true,
      loading: false,
      error: null
    })
  ),
  on(EmployeeActions.loadEmployeesFail, (state, { errors }) => ({
    ...state,
    error: errors,
    loaded: false,
    loading: false,
  })),
  on(EmployeeActions.clearEmployees,
    state => adapter.removeAll(state)
  ),
);

export const getSelectedEmployeeId = (state: State) => state.selectedEmployeeId;
export const getLoadedEmployee = (state: State) => state.loaded;
export const getLoadingEmployee = (state: State) => state.loading;
export const getError = (state: State) => state.error;

export const {
  selectIds,
  selectEntities,
  selectAll,
  selectTotal,
} = adapter.getSelectors();

// select the array of employees ids
export const selectEmployeeIds = selectIds;

// select the dictionary of employee entities
export const selectEmployeeEntities = selectEntities;

// select the array of employees
export const selectAllEmployees = selectAll;

// select the total employees count
export const selectEmployeesTotal = selectTotal;
