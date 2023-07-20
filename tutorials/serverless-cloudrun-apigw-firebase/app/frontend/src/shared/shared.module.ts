import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule } from '@angular/forms';

// components
import { AuthFormComponent } from './components/auth-form/auth-form.component';

// guards
import { AuthGuard } from './guards/auth.guard';

// import fontawesome
import { FontAwesomeModule } from '@fortawesome/angular-fontawesome';

// Angular Material
import { MatButtonModule } from "@angular/material/button";
import { MatToolbarModule } from "@angular/material/toolbar";
import { MatIconModule } from "@angular/material/icon";
import { MatCardModule } from "@angular/material/card";
import { MatSidenavModule } from "@angular/material/sidenav";
import { MatListModule } from "@angular/material/list";
import { MatDialogModule } from "@angular/material/dialog";
import { MatInputModule } from "@angular/material/input";
import { MatSelectModule } from "@angular/material/select";
import { MatDividerModule } from "@angular/material/divider";
import { MatProgressBarModule } from "@angular/material/progress-bar";
import { MatProgressSpinnerModule } from "@angular/material/progress-spinner";

@NgModule({
  imports: [
    CommonModule,
    ReactiveFormsModule,
    FontAwesomeModule,
    MatButtonModule,
    MatToolbarModule,
    MatIconModule,
    MatCardModule,
    MatSidenavModule,
    MatListModule,
    MatDialogModule,
    MatInputModule,
    MatSelectModule,
    MatDividerModule,
    MatProgressBarModule,
    MatProgressSpinnerModule,
  ],
  declarations: [
    AuthFormComponent
  ],
  exports: [
    FontAwesomeModule,
    AuthFormComponent,
    MatButtonModule,
    MatToolbarModule,
    MatIconModule,
    MatCardModule,
    MatSidenavModule,
    MatListModule,
    MatDialogModule,
    MatInputModule,
    MatSelectModule,
    MatDividerModule,
    MatProgressBarModule,
    MatProgressSpinnerModule,
  ],
  providers: [
    AuthGuard
  ]
})
export class SharedModule {
  constructor() {
    // library.add(faSpinnerThird, faDumbbell);
  }
}
