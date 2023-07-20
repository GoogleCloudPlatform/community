import { Injectable } from '@angular/core';
import { MatDialog, MatDialogRef } from '@angular/material/dialog';
import { DEFAULT_CONFIG, DialogConfig } from 'src/interfaces/dialog-config.interface';
import { DeleteEmployeeComponent } from '../components';
import { DataInterface } from 'src/interfaces/employee.interface';

// Store
import { Store } from '@ngrx/store';
import * as fromStore from '../store';


@Injectable({
  providedIn: 'root'
})
export class DeleteEmployeeDialogService {

  // reference to the Delete Employee Dialog Component
  dialogRef: MatDialogRef<DeleteEmployeeComponent>;

  constructor(private dialog: MatDialog,
              private store: Store<fromStore.EmployeeState>) {}

  openFormDialog(config?: DialogConfig): void {

    // Override default configuration, if existing
    const dialogConfig = { ... DEFAULT_CONFIG, ... config };

    this.dialogRef = this.dialog.open(DeleteEmployeeComponent, dialogConfig);

    this.dialogRef.afterClosed()
      .subscribe((data: DataInterface) => {
        this.store.dispatch(fromStore.deleteEmployee({ id: data.currentEmployee.id! }));
      });
  }

}
