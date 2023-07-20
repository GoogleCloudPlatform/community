import { ChangeDetectionStrategy, Component, Inject, OnInit } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef } from '@angular/material/dialog';
import { DataInterface } from 'src/interfaces/employee.interface';
import { UntypedFormBuilder, UntypedFormGroup } from '@angular/forms';


@Component({
  selector: 'app-employee-dialog-form',
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './employee-dialog-form.component.html',
  styleUrls: ['./employee-dialog-form.component.scss']
})
export class EmployeeDialogFormComponent implements OnInit {

  form: UntypedFormGroup;
  jobTitles: string[] = [
    'Analyst',
    'Associate Partner',
    'Client Delivery Lead',
    'Cloud Architect',
    'Cloud Engineer',
    'Partner',
    'Program Manager',
    'Project Manager',
    'Senior Cloud Architect',
    'Senior Cloud Engineer',
    'Senior Partner',
    'Senior Project Manager'
  ];



  constructor(private fb: UntypedFormBuilder,
              private dialogRef: MatDialogRef<EmployeeDialogFormComponent>,
              @Inject(MAT_DIALOG_DATA) private data: DataInterface) { }

  ngOnInit(): void {
    // console.log(this.data);

    this.form = this.fb.group({
      firstName: this.data.currentEmployee ? this.data.currentEmployee.firstName : '',
      lastName: this.data.currentEmployee ? this.data.currentEmployee.lastName : '',
      jobTitle: this.data.currentEmployee ? this.data.currentEmployee.jobTitle : '',
      city: this.data.currentEmployee.address?.city ? this.data.currentEmployee.address.city : '',
      street: this.data.currentEmployee.address?.street ? this.data.currentEmployee.address.street : '',
      avatarURL: this.data.currentEmployee ? this.data.currentEmployee.avatarURL : '',
      imageURL: this.data.currentEmployee ? this.data.currentEmployee.imageURL : '',
      yearsExperience: this.data.currentEmployee ? this.data.currentEmployee.yearsExperience : ''
    });
  }


}

