import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';
import { RouterModule, Routes } from "@angular/router";
import { BrowserAnimationsModule}  from "@angular/platform-browser/animations";
import { HTTP_INTERCEPTORS, HttpClientModule } from '@angular/common/http';

import * as fromContainers from './containers';

import { AuthModule } from "../auth/auth.module";
import { SharedModule } from "../shared/shared.module";
import { EmployeeModule } from "../employee/employee.module";

// Routes
export const ROUTES: Routes = [
  { path: '', pathMatch: 'full', redirectTo: '/employee' },
  { path: 'redirectToRoot', redirectTo: '/'},
  { path: '**', redirectTo: '/employee'}
];

// this would be done dynamically with webpack for builds
const environment = {
  development: true,
  production: false,
};

// Store Imports
import { reducers } from '../store';
import { MetaReducer, StoreModule } from '@ngrx/store';
import { StoreDevtoolsModule } from '@ngrx/store-devtools';
import { EffectsModule } from '@ngrx/effects';
import { StoreRouterConnectingModule, RouterStateSerializer } from '@ngrx/router-store';
import { CustomSerializer } from '../store/reducers/router.reducer';
import { storeFreeze } from 'ngrx-store-freeze';
import { TokenInterceptor } from "../shared/interceptors/token.interceptor";
export const metaReducers: MetaReducer<any>[] = !environment.production
  ? [storeFreeze]
  : [];

@NgModule({
  declarations: [
    ...fromContainers.containers
  ],
  imports: [
    BrowserModule,
    BrowserAnimationsModule,
    RouterModule.forRoot(ROUTES, {}),
    StoreModule.forRoot({}, { metaReducers }),
    StoreModule.forFeature('appRoot', reducers),
    StoreDevtoolsModule.instrument({ maxAge: 25, logOnly: environment.production }),
    EffectsModule.forRoot([]),
    StoreRouterConnectingModule.forRoot(),
    HttpClientModule,
    AuthModule,
    SharedModule,
    EmployeeModule
  ],
  providers: [
    { provide: RouterStateSerializer, useClass: CustomSerializer },
    {
      provide: HTTP_INTERCEPTORS,
      useClass: TokenInterceptor,
      multi: true
    }
  ],
  bootstrap: [fromContainers.AppComponent]
})
export class AppModule { }
