import { Injectable } from '@angular/core';
import { MatDialog, MatDialogRef } from '@angular/material/dialog';
import { EmployeeDialogFormComponent } from '../components';
import { DEFAULT_CONFIG, DialogConfig } from 'src/interfaces/dialog-config.interface';
import { Employee } from 'src/interfaces/employee.interface';
import { Store } from '@ngrx/store';
import * as fromStore from '../store';


@Injectable({
  providedIn: 'root'
})
export class CreateEmployeeDialogService {

  // reference to the Employee Dialog Form Component
  dialogRef: MatDialogRef<EmployeeDialogFormComponent>;

  getRandomInt(max: number): number {
    return Math.floor(Math.random() * max);
  }

  constructor(private dialog: MatDialog,
              private store: Store<fromStore.EmployeeState>) {}

  openFormDialog(config?: DialogConfig): void {

    // Override default configuration, if existing
    const dialogConfig = { ... DEFAULT_CONFIG, ... config };

    this.dialogRef = this.dialog.open(EmployeeDialogFormComponent, dialogConfig);

    this.dialogRef.afterClosed()
      .subscribe((data) => {
        const employee: Employee = {
          id: ""+this.getRandomInt(100000),
          firstName: data.firstName,
          lastName: data.lastName,
          jobTitle: data.jobTitle,
          avatarURL: data.avatarURL,
          imageURL: data.imageURL,
          yearsExperience: data.yearsExperience,
          address: {
            city: data.city,
            street: data.street
          }
        };

        this.store.dispatch(fromStore.addEmployee({ employee }));
      });
  }

}
