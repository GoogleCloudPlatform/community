import { Injectable } from '@angular/core';
import { Actions, createEffect, ofType } from '@ngrx/effects';
import { of } from 'rxjs';
import { map, catchError, switchMap, tap } from 'rxjs/operators';

import { FirestoreService } from 'src/employee/services/firestore.service';
import { SnackbarService } from 'src/employee/services/snackbar.service';

import * as employeeActions from '../actions/employee.actions';

@Injectable()
export class EmployeeEffects {

  constructor(
    private actions$: Actions,
    private firestoreService: FirestoreService,
    private snackbarService: SnackbarService
  ) {}

  loadEmployees$ = createEffect(() =>
    this.actions$.pipe(
      ofType(employeeActions.loadEmployees),
      switchMap(() => this.firestoreService.getEmployees()
        .pipe(
          map(employees => employeeActions.loadEmployeesSuccess({ employees })),
          catchError( error => of(employeeActions.loadEmployeesFail({ errors: error })))
        ))
    )
  );

  addEmployee$ = createEffect(() =>
    this.actions$.pipe(
      ofType(employeeActions.addEmployee),
      switchMap(({ employee }) => this.firestoreService.addEmployee(employee)
        .pipe(
          map(() => employeeActions.addEmployeeSuccess()),
          catchError(error => of(employeeActions.addEmployeeFail({ errors: error })))
        ))
    )
  );

  addEmployeeSuccess$ = createEffect(() =>
    this.actions$.pipe(
      ofType(employeeActions.addEmployeeSuccess),
      tap( () => this.snackbarService.openSnackbar('Employee Added Successfully!', {
        closable: false,
        severity: 'info',
        duration: 2000
      }))
    ), { dispatch: false }
  );

  deleteEmployee$ = createEffect(() =>
    this.actions$.pipe(
      ofType(employeeActions.deleteEmployee),
      switchMap((action) => this.firestoreService.deleteEmployee(action.id)
        .pipe(
          map(() => employeeActions.deleteEmployeeSuccess()),
          catchError(error => of(employeeActions.deleteEmployeeFail({ errors: error })))
        ))
    )
  );

  deleteEmployeeSuccess$ = createEffect(() =>
    this.actions$.pipe(
      ofType(employeeActions.deleteEmployeeSuccess),
      tap( () => this.snackbarService.openSnackbar('Employee Deleted Successfully!', {
        closable: false,
        severity: 'info',
        duration: 2000
      }))
    ), { dispatch: false }
  );

  // performDelete(id: number): Observable<Action> {
  //   return this.firestoreService.deleteEmployee(id)
  //     .pipe(
  //       map(() => employeeActions.deleteEmployeeSuccess()),
  //       catchError(error => of(employeeActions.deleteEmployeeFail({ errors: error })))
  //     );
  // }

}
