import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Routes } from "@angular/router";
import { AuthGuard } from "../shared/guards/auth.guard";
import { ReactiveFormsModule } from '@angular/forms';

// shared module
import { SharedModule } from 'src/shared/shared.module';

import * as fromComponents from './components';
import * as fromContainers from './containers';

// Import Store Module
import { StoreModule } from '@ngrx/store';
import { EffectsModule } from '@ngrx/effects';
import { reducers, effects } from './store';

// Services
import { SnackbarService } from './services/snackbar.service';

// routes
export const ROUTES: Routes = [
  { path: 'employee',
    canActivate: [AuthGuard],
    component: fromContainers.MainComponent },
];

@NgModule({
    declarations: [
        ...fromContainers.containers,
        ...fromComponents.components
    ],
    imports: [
        RouterModule.forChild(ROUTES),
        CommonModule,
        SharedModule,
        StoreModule.forFeature('EmployeeState', reducers),
        EffectsModule.forFeature(effects),
        ReactiveFormsModule
    ],
    providers: [
        SnackbarService
    ]
})
export class EmployeeModule { }
