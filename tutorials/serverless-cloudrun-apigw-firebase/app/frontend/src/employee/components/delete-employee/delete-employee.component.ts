import { ChangeDetectionStrategy, Component, Inject, OnInit } from '@angular/core';
import { MAT_DIALOG_DATA, MatDialogRef} from '@angular/material/dialog';
import { DataInterface } from 'src/interfaces/employee.interface';

@Component({
  selector: 'app-delete-employee',
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './delete-employee.component.html',
  styleUrls: ['./delete-employee.component.scss']
})
export class DeleteEmployeeComponent implements OnInit {

  constructor(private dialogRef: MatDialogRef<DeleteEmployeeComponent>,
              @Inject(MAT_DIALOG_DATA) public data: DataInterface) { }

  ngOnInit(): void {
  }

}
