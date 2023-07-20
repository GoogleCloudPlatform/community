import {Component, inject, OnInit} from '@angular/core';
import { UntypedFormGroup } from '@angular/forms';
import { Router } from '@angular/router';
import { Observable } from 'rxjs';
import { Auth } from '@angular/fire/auth';

// import Store
import { Store } from '@ngrx/store';
import * as fromStore from '../../../store';

import { EmployeeCredentials } from "../../../../interfaces/employee.interface";

import { faHourglass } from '@fortawesome/free-regular-svg-icons';

@Component({
  selector: 'register',
  templateUrl: 'register.component.html'
})
export class RegisterComponent implements OnInit {

  private auth: Auth = inject(Auth);

  // if firebase does not return an error, the error string will be empty
  // and there wont' be any message displayed..
  error: string;
  showPasswordInput = true;
  loading: Observable<boolean>;
  formIsValid: boolean;
  faHourglass = faHourglass;

  constructor(private store: Store<fromStore.AuthState>, private router: Router) {}

  ngOnInit(): void {
    this.loading = this.store.select(fromStore.getAuthenticationLoading);
  }

  async registerUser(event: UntypedFormGroup) {
    const { email, password } = event.value;
    const creds: EmployeeCredentials = {
      email: email,
      password: password
    };

    try {
      // register user
      await this.store.dispatch(fromStore.register({ payload: creds }));
      // THEN
      this.router.navigate(['/']);
    } catch (err: any) {
      this.error = err.message;
    }
  }

  async SignupWithGoogle() {
    try {
      // then...
      await this.store.dispatch(fromStore.googleLogin());
    } catch (err: any) {
      console.log(err.message);
    }
  }

  isFormValid(isValid: boolean) {
    this.formIsValid = isValid;
  }
}
