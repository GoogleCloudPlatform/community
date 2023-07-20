import { Injectable } from '@angular/core';
import { Router } from '@angular/router';

import { Actions, ofType, createEffect} from '@ngrx/effects';

import { map, switchMap, catchError, tap } from 'rxjs/operators';
import { from, of } from 'rxjs';

import { Employee } from "../../../interfaces/employee.interface";
import * as authActions from '../actions/auth.actions';

// import firebase
import {
  getAuth,
  signInWithEmailAndPassword,
  signInWithPopup,
  GoogleAuthProvider,
  signOut,
  createUserWithEmailAndPassword,
  sendPasswordResetEmail,
  authState
} from '@angular/fire/auth';


@Injectable()
export class AuthEffects {
  constructor(
    private actions$: Actions,
    private router: Router) {
  }


  login$ = createEffect(() => this.actions$.pipe(
    ofType(authActions.login),
    map( action => action.payload ),
    switchMap( payload => {
      const auth = getAuth();
      return from(signInWithEmailAndPassword(auth, payload.email, payload.password))
        .pipe(
          map(credential => authActions.loginSuccess()),
          catchError( error => of(authActions.loginFail({ errors: error })))
        )
    })
  ));

  signup$ = createEffect(() => this.actions$.pipe(
    ofType(authActions.register),
    map( action => action.payload ),
    switchMap( payload => {
      const auth = getAuth();
      return from(createUserWithEmailAndPassword(auth, payload.email, payload.password))
        .pipe(
          map(credential => authActions.registerSuccess()),
          catchError( error => of(authActions.registerFail({ errors: error })))
        )
    })
  ));

  googleLogin$ = createEffect(() => this.actions$.pipe(
    ofType(authActions.googleLogin),
    switchMap(() => {
      const provider = new GoogleAuthProvider();
      const auth = getAuth();
      return from(signInWithPopup(auth, provider))
        .pipe(
          map(credentials => authActions.googleLoginSuccess()),
          catchError(error => of(authActions.googleLoginFail({ errors: error })))
        );
    })
  ));

  logoutUser$ = createEffect(() => this.actions$.pipe(
    ofType(authActions.logout),
    switchMap(() => {
      const auth = getAuth();
      return from(signOut(auth))
        .pipe(
          map(() => authActions.logoutSuccess()),
          catchError (error => of(authActions.logoutFail({ errors: error })))
        );
    })
  ));

  redirectAfterUserAuthenticated$ = createEffect(() => this.actions$.pipe(
    ofType(authActions.authenticated),
    tap(() => this.router.navigate(['/']))),
    { dispatch: false }
  );

  forgotPassword$ = createEffect(() => this.actions$.pipe(
    ofType(authActions.forgotPassword),
    map( action => action.payload ),
    switchMap( payload => {
      const auth = getAuth();
      return from(sendPasswordResetEmail(auth, payload.email))
        .pipe(
          map(() => authActions.forgotPasswordSuccess()),
          catchError(error => of(authActions.forgotPasswordFail( { errors: error })))
        )
    })
  ));

  getUser$ = createEffect(() => this.actions$.pipe(
    ofType(authActions.googleLoginSuccess || authActions.loginSuccess || authActions.registerSuccess),
    switchMap(() => {
      const auth = getAuth();
      return authState(auth)
        .pipe(
          // filter(user => !!user),
          map(authData => {
            if (authData) {
              // user logged in
              const employee: Employee = {
                displayName: authData.displayName ? authData.displayName : undefined,
                email: authData.email ? authData.email : undefined,
                id: authData.uid ? authData.uid : undefined,
                imageURL: authData.photoURL ? authData.photoURL : undefined,
                authenticated: true
              };
              return authActions.authenticated({ employee });
            } else {
              return authActions.notAuthenticated();
            }
          })
        );
    })
  ));

}
