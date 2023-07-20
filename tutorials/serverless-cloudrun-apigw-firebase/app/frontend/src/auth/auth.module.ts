import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterModule, Routes } from '@angular/router';

// third-party modules
import { environment } from '../environments/environment';
import { provideFirebaseApp, initializeApp } from '@angular/fire/app';
import { getAuth, provideAuth } from '@angular/fire/auth';
import { getFirestore, provideFirestore } from '@angular/fire/firestore';

// shared module
import { SharedModule } from '../shared/shared.module';

// Import Store Module
import { StoreModule } from '@ngrx/store';
import { EffectsModule } from '@ngrx/effects';
import { reducers, effects } from './store';

// routes
export const ROUTES: Routes = [
    {
        path: 'auth',
        children: [
          { path: '', pathMatch: 'full', redirectTo: 'login' },
          { path: 'login', loadChildren: () => import('./login/login.module').then(m => m.LoginModule) },
          { path: 'register', loadChildren: () => import('./register/register.module').then(m => m.RegisterModule) },
          { path: 'forgot', loadChildren: () => import('./forgot/forgot.module').then(m => m.ForgotModule) },
          { path: '**', redirectTo: 'login'}
        ]
    }
];

@NgModule({
    imports: [
      CommonModule,
      RouterModule.forChild(ROUTES),
      provideFirebaseApp(() => initializeApp(environment.firebase)),
      provideAuth(() => getAuth()),
      provideFirestore(() => getFirestore()),
      StoreModule.forFeature('AuthState', reducers),
      EffectsModule.forFeature(effects),
      SharedModule
    ],
    declarations: [],
    providers: [effects]
})
export class AuthModule {}
