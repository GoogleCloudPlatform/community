import { Component, OnInit } from '@angular/core';
import { Observable} from 'rxjs';
import { Employee } from 'src/interfaces/employee.interface';
import { CreateEmployeeDialogService } from 'src/employee/services/create-employee-dialog.service';
import { faker } from '@faker-js/faker';

// Store
import { Store } from '@ngrx/store';
import * as fromStore from '../../store';

@Component({
  selector: 'app-main',
  templateUrl: './main.component.html',
  styleUrls: ['./main.component.scss']
})
export class MainComponent implements OnInit {

  employees$: Observable<Employee[]>;
  loading$: Observable<boolean>;

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

  constructor(private store: Store<fromStore.EmployeeState>,
              private dialogFormService: CreateEmployeeDialogService) {
  }

  ngOnInit(): void {
    this.store.dispatch(fromStore.loadEmployees());
    this.employees$ = this.store.select(fromStore.selectAllEmployees);
    this.loading$ = this.store.select(fromStore.getEmployeesLoading);
  }

  openDialog(): void {

    this.dialogFormService.openFormDialog({
      data: {
        currentEmployee: {
          firstName: faker.name.firstName(),
          lastName: faker.name.lastName(),
          avatarURL: faker.image.avatar(),
          imageURL: faker.image.business(),
          yearsExperience: faker.datatype.number({ min: 1, max: 20 }),
          jobTitle: this.jobTitles[Math.floor(Math.random() * this.jobTitles.length)],
          address: {
            city: faker.address.city(),
            street: faker.address.streetName()
          }
        }
      }
    });
  }

}
