import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Routes } from '@angular/router';

import { SharedModule } from '../../shared/shared.module';

import { ForgotComponent } from './containers/forgot/forgot.component';

export const ROUTES: Routes =
  [
    { path: '', component: ForgotComponent }
  ];

@NgModule({
  imports: [
    CommonModule,
    SharedModule,
    RouterModule.forChild(ROUTES)
  ],
  declarations: [
    ForgotComponent
  ]
})
export class ForgotModule {}
