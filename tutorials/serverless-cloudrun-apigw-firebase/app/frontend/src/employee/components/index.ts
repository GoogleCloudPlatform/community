import { DeleteEmployeeComponent } from './delete-employee/delete-employee.component';
import { EmployeeDialogFormComponent } from './employee-dialog-form/employee-dialog-form.component';
import { EmployeeComponent } from './employee/employee.component';
import { EmployeesListComponent } from './employees-list/employees-list.component';
import { SnackbarComponent } from './snackbar/snackbar.component';
import { SpinnerComponent } from './spinner/spinner.component';

export const components: any[] = [
  EmployeeComponent,
  DeleteEmployeeComponent,
  EmployeeDialogFormComponent,
  EmployeesListComponent,
  SnackbarComponent,
  SpinnerComponent
];

export * from './employee/employee.component';
export * from './delete-employee/delete-employee.component';
export * from './employee-dialog-form/employee-dialog-form.component';
export * from './employees-list/employees-list.component';
export * from './snackbar/snackbar.component';
export * from './spinner/spinner.component';
