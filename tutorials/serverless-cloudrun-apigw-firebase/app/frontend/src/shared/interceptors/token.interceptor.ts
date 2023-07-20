import { Injectable } from '@angular/core';
import {
  HttpRequest,
  HttpHandler,
  HttpEvent,
  HttpInterceptor
} from '@angular/common/http';

import { from, Observable } from "rxjs";
import { getAuth, onAuthStateChanged } from "@angular/fire/auth";
import { switchMap } from "rxjs/operators";

@Injectable()
export class TokenInterceptor implements HttpInterceptor {

  // userToken: string;

  constructor() {}
  intercept(request: HttpRequest<any>, next: HttpHandler): Observable<HttpEvent<any>> {

    return from(this.getToken())
      .pipe(
        switchMap(token => {
          request = request.clone({
            setHeaders: {
              Authorization: `Bearer ${token}`
            }
          });
          return next.handle(request);
        })
      )

  }

  getToken(): Promise<string> {
    return new Promise((resolve, reject) => {
      const auth = getAuth();
      onAuthStateChanged( auth,user => {
        if (user) {
          user.getIdToken().then(idToken => resolve(idToken));
        }
      }, reject);
    })
  }
}
