import {ChangeDetectionStrategy, Component, EventEmitter, Input, OnDestroy, OnInit, Output} from '@angular/core';
import { UntypedFormBuilder, UntypedFormGroup, Validators } from '@angular/forms';
import { Subscription } from 'rxjs';
import { debounceTime, distinctUntilChanged } from 'rxjs/operators';

@Component({
  // tslint:disable-next-line:component-selector
  selector: 'auth-form',
  styleUrls: ['auth-form.component.scss'],
  templateUrl: 'auth-form.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush
})
export class AuthFormComponent implements OnInit, OnDestroy {

  subscription: Subscription;

  constructor(private fb: UntypedFormBuilder) {}

  @Input()
  showPasswordInput: boolean;

  @Output()
  submitted = new EventEmitter<UntypedFormGroup>();

  @Output()
  formIsValid = new EventEmitter<boolean>();

  form = this.fb.group({
    email: ['', Validators.email],
    // password: ['', Validators.required]
    password: ['']
  });

  ngOnInit(): void {
    this.form.reset();
    this.onChanges();
  }

  onSubmit() {
    if (this.form.valid) {
      // emit
      this.submitted.emit(this.form);
      this.form.reset(this.form.value);
    }
  }

  get passwordInvalid() {
    const control = this.form.get('password');
    // @ts-ignore
    return control.hasError('required') && control.touched;
  }

  get emailFormat() {
    const control = this.form.get('email');
    // @ts-ignore
    return control.hasError('email') && control.touched;
  }

  onChanges(): void {
    this.subscription = this.form.statusChanges
      .pipe(
        debounceTime(200),
        distinctUntilChanged()
      )
      .subscribe(status => status === 'INVALID' ? this.formIsValid.emit(false) : this.formIsValid.emit(true));
  }

  ngOnDestroy(): void {
    this.subscription.unsubscribe();
  }
}
