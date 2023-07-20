import { Component, OnInit } from '@angular/core';
import { Router, RouterEvent, NavigationStart, NavigationEnd} from '@angular/router';

import { filter, map, share } from "rxjs/operators";
import { Observable } from "rxjs";
import { BreakpointObserver, Breakpoints } from "@angular/cdk/layout";

// import Store
import { Store } from '@ngrx/store';
import * as fromStore from '../../../auth/store';

import { Employee } from "../../../interfaces/employee.interface";

import { faArrowAltCircleRight } from '@fortawesome/free-regular-svg-icons';

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.scss']
})
export class AppComponent implements OnInit {

  loading: boolean;
  employee$: Observable<Employee>;
  faArrowAltCircleRight = faArrowAltCircleRight;

  isHandset$: Observable<boolean> = this.breakpointObserver.observe(Breakpoints.Handset)
    .pipe(
      map(result => result.matches),
      share()
    );

  constructor(private store: Store<fromStore.AuthState>,
              private router: Router,
              private breakpointObserver: BreakpointObserver) {
    this.loading = false;

    router.events.pipe(
      filter((event): event is RouterEvent => event instanceof NavigationEnd || event instanceof NavigationStart)
    ).subscribe((e: RouterEvent) => {
      if (e instanceof NavigationStart) {
        this.loading = true;
      } else if (e instanceof NavigationEnd) {
        this.loading = false;
      }
    });

  }

  ngOnInit(): void {
    this.employee$ = this.store.select(fromStore.getAuthenticationEmployee);
  }

  async onLogout() {
    await this.store.dispatch(fromStore.logout());
    await this.router.navigate(['/auth/login']);
  }

}
