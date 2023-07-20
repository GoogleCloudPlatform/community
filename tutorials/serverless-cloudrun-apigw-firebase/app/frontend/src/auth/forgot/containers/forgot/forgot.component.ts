import { Component, OnInit } from '@angular/core';
import { UntypedFormGroup } from '@angular/forms';

import { Observable } from 'rxjs';

// import Store
import { Store } from '@ngrx/store';
import * as fromStore from '../../../store';

import { faHourglass } from '@fortawesome/free-regular-svg-icons';

@Component({
  // tslint:disable-next-line:component-selector
  selector: 'forgot',
  templateUrl: 'forgot.component.html'
})
export class ForgotComponent implements OnInit {

  loading: Observable<boolean>;
  formError: string;
  showPasswordInput = false;
  formIsValid: boolean;
  faHourglass = faHourglass;

  constructor(private store: Store<fromStore.AuthState>) {}

  ngOnInit(): void {
    this.loading = this.store.select(fromStore.getAuthenticationLoading);
  }

  async resetPassword(event: UntypedFormGroup) {

    const { email } = event.value;
    try {
      // then...
      await this.store.dispatch(fromStore.forgotPassword(email));

    } catch (err: any) {
      this.formError = err.message;
    }

  }

  isFormValid(isValid: boolean) {
    this.formIsValid = isValid;
  }

}
