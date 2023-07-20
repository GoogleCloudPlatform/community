import { createSelector } from '@ngrx/store';

import * as fromFeature from '../reducers';
import * as fromEmployee from '../reducers/employee.reducer';
import { Employee } from 'src/interfaces/employee.interface';

export const selectEmployeeState = createSelector(
  fromFeature.getAppState, (state: fromFeature.EmployeeState) => state.employeesState);

export const selectEmployeesIds = createSelector(
  selectEmployeeState,
  fromEmployee.selectEmployeeIds // shorthand for usersState => fromUser.selectUserIds(usersState)
);
export const selectEmployeeEntities = createSelector(
  selectEmployeeState,
  fromEmployee.selectEmployeeEntities
);
export const selectAllEmployees = createSelector(
  selectEmployeeState,
  fromEmployee.selectAllEmployees
);
export const selectUserTotal = createSelector(
  selectEmployeeState,
  fromEmployee.selectEmployeesTotal
);
export const selectCurrentEmployeeId = createSelector(
  selectEmployeeState,
  fromEmployee.getSelectedEmployeeId
);

export const selectCurrentUser = createSelector(
  selectEmployeeEntities,
  selectCurrentEmployeeId,
  (employeeEntities, userId): Employee | undefined => {
    if (userId != null) {
      return employeeEntities[userId];
    } else {
      return undefined;
    }
  }
);

export const getEmployeesLoading = createSelector(selectEmployeeState, fromEmployee.getLoadingEmployee);
export const getEmployeesLoaded = createSelector(selectEmployeeState, fromEmployee.getLoadedEmployee);
export const getEmployeesErrors = createSelector(selectEmployeeState, fromEmployee.getError);
