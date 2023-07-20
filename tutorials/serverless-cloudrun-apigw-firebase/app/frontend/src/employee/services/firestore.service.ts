import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { Employee } from 'src/interfaces/employee.interface';

// import { environment } from '../../environments/environment';



@Injectable({
  providedIn: 'root'
})
export class FirestoreService {

  // gp-service-project
  // addEmployeeUrl = 'https://amazing-employees-api-d8cina3u.ue.gateway.dev/employee';
  // employeesUrl = 'https://amazing-employees-api-d8cina3u.ue.gateway.dev/employees';
  // deleteEmployeeUrl = 'https://amazing-employees-api-d8cina3u.ue.gateway.dev/employee';

  // gcp-three-tier-ref-app project - terraform
  addEmployeeUrl = 'https://employee-gateway-88s1idnh.ue.gateway.dev/employee';
  employeesUrl = 'https://employee-gateway-88s1idnh.ue.gateway.dev/employees';
  deleteEmployeeUrl = 'https://employee-gateway-88s1idnh.ue.gateway.dev/employee';

  // gcp-three-tier-ref-app project - gcloud

  // addEmployeeUrl = 'https://amazing-employees-api-88s1idnh.ue.gateway.dev/employee';
  // employeesUrl = 'https://amazing-employees-api-88s1idnh.ue.gateway.dev/employees';
  // deleteEmployeeUrl = 'https://amazing-employees-api-88s1idnh.ue.gateway.dev/employee';



  constructor(private http: HttpClient) { }

  employees: Employee[];

  getEmployees(): Observable<Employee[]> {
    return this.http
      .get<Employee[]>(this.employeesUrl);
  }

  addEmployee(employee: Employee): Observable<any> {
    return this.http
      .post(this.addEmployeeUrl, { ...employee });
  }

  deleteEmployee(id: string): Observable<any> {
    const deleteUrl = this.deleteEmployeeUrl + '?id=' + id;
    return this.http
      .delete(deleteUrl);
  }
}


