import { Injectable } from '@angular/core';
import { Router, CanActivate, ActivatedRouteSnapshot, RouterStateSnapshot, UrlTree } from '@angular/router';
import { Observable } from 'rxjs';
import { Store, select } from '@ngrx/store';
import { map, take } from 'rxjs/operators';

// import auth store
import * as fromAuth from '../../auth/store';

@Injectable({
  providedIn: 'root',
})
export class AuthGuard implements CanActivate {
  constructor(private router: Router, private store: Store<fromAuth.AuthState> ) {}

  canActivate(next: ActivatedRouteSnapshot, state: RouterStateSnapshot): Observable<boolean | UrlTree> {
    return this.store.pipe(
      select(fromAuth.getAuthenticationEmployee),
      map(user => {
        if (!user || !user.id) {
          // this.router.navigate(['/auth/login']);
          return this.router.parseUrl('/auth/login');
          // return false;
        } else {
          return true;
        }
      }),
      take(1)
    );
  }

}
