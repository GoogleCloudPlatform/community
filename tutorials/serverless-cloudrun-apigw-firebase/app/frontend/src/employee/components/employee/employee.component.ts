import { Component, OnInit, ChangeDetectionStrategy, Input} from '@angular/core';
import { Employee } from 'src/interfaces/employee.interface';
import { DeleteEmployeeDialogService } from 'src/employee/services/delete-employee-dialog.service';

@Component({
  selector: 'app-employee',
  templateUrl: './employee.component.html',
  styleUrls: ['./employee.component.scss'],
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class EmployeeComponent implements OnInit {
  @Input() employeeDetails: Employee;

  constructor(private dialogFormService: DeleteEmployeeDialogService) { }

  ngOnInit(): void {
  }

  onDelete(): void {
    this.dialogFormService.openFormDialog({
      data: {
        currentEmployee: this.employeeDetails
      }
    });
  }

}
