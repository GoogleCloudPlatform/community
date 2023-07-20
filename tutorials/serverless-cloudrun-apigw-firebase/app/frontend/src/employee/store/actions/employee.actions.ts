import { createAction, props } from '@ngrx/store';
import { Update } from '@ngrx/entity';

import { Employee } from 'src/interfaces/employee.interface';

export const loadEmployees = createAction('[Employee/API] LOAD Employees');
export const loadEmployeesSuccess = createAction('[Employee/API] LOAD Employees SUCCESS', props<{ employees: Employee[] }>());
export const loadEmployeesFail = createAction('[Employee/API] LOAD Employees FAIL', props<{ errors: any }>());

export const deleteEmployee = createAction('[Employee/API] Delete Employee', props<{ id: string }>());
export const deleteEmployeeSuccess = createAction('[Employee/API] Delete Employee SUCCESS');
export const deleteEmployeeFail = createAction('[Employee/API] Delete Employee FAIL', props<{ errors: any }>());

export const addEmployee = createAction('[Employee/API] Add Employee', props<{ employee: Employee }>());
export const addEmployeeSuccess = createAction('[Employee/API] Add Employee SUCCESS');
export const addEmployeeFail = createAction('[Employee/API] Add Employee FAIL', props<{ errors: any }>());

export const upsertEmployee = createAction(
  '[Employee/API] Upsert Employee',
  props<{ employee: Employee }>()
);

export const addEmployees = createAction(
  '[Employee/API] Add Employees',
  props<{ employees: Employee[] }>()
);

export const upsertEmployees = createAction(
  '[Employee/API] Upsert Employees',
  props<{ employees: Employee[] }>()
);

export const updateEmployee = createAction(
  '[Employee/API] Update Employee',
  props<{ employee: Update<Employee> }>()
);

export const updateEmployees = createAction(
  '[Employee/API] Update Employees',
  props<{ employees: Update<Employee>[] }>()
);

export const deleteEmployees = createAction(
  '[Employee/API] Delete Employees',
  props<{ ids: string[] }>()
);

export const clearEmployees = createAction(
  '[Employee/API] Clear Employees'
);
