import { Component, inject, OnInit } from '@angular/core';
import { UntypedFormGroup } from '@angular/forms';
import { Observable } from 'rxjs';
import { Auth } from '@angular/fire/auth';

// import Store
import { Store } from '@ngrx/store';
import * as fromStore from '../../../store';
import { EmployeeCredentials } from "../../../../interfaces/employee.interface";

import { faHourglass } from '@fortawesome/free-regular-svg-icons';

@Component({
  // tslint:disable-next-line:component-selector
  selector: 'login',
  templateUrl: 'login.component.html'
})
export class LoginComponent implements OnInit {

  private auth: Auth = inject(Auth);

  loading: Observable<boolean>;
  showPasswordInput = true;
  formError: string;
  authenticationError: Observable<any>;
  formIsValid: boolean;
  faHourglass = faHourglass;

  constructor(private store: Store<fromStore.AuthState>) {}

  ngOnInit() {
    this.loading = this.store.select(fromStore.getAuthenticationLoading);
    this.authenticationError = this.store.select(fromStore.getAuthenticationErrors);
  }

  async loginUser(event: UntypedFormGroup) {
    const { email, password } = event.value;
    const creds: EmployeeCredentials = {
      email: email,
      password: password
    }
    try {
      // then...
      await this.store.dispatch(fromStore.login({ payload: creds }));

    } catch (err: any) {
      this.formError = err.message;
    }
  }

  async loginUserWithGoogle() {
    try {
      // then...
      await this.store.dispatch(fromStore.googleLogin());
    } catch (err: any) {
      this.formError = err.message;
    }
  }

  isFormValid(isValid: boolean) {
    this.formIsValid = isValid;
  }
}
