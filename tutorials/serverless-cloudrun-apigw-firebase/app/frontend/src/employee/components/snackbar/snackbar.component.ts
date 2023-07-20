import { Component, OnInit } from '@angular/core';
import { trigger, state, style, transition, animate } from '@angular/animations';
import { SnackbarOptions} from './snackbar-options';
import { Subject } from 'rxjs';

@Component({
  selector: 'app-snackbar',
  templateUrl: './snackbar.component.html',
  styleUrls: ['./snackbar.component.scss'],
  animations: [
    trigger('feedbackAnimation', [
      state(
        'void',
        style({
          transform: 'translateY(100%)',
          opacity: 0
        })
      ),
      state(
        '*',
        style({
          transform: 'translateY(0)',
          opacity: 1
        })
      ),
      transition('* <=> void', animate(`400ms cubic-bezier(0.4, 0, 0.1, 1)`))
    ])
  ],
})
export class SnackbarComponent implements OnInit {

  private durationTimeoutId: any;

  private onDestroy = new Subject<void>();
  onDestroy$ = this.onDestroy.asObservable();

  message: string;
  options: SnackbarOptions;
  animationState: '*' | 'void' = 'void';

  constructor() { }

  ngOnInit(): void {}

  open(message: string, options: SnackbarOptions): void {
    this.message = message;
    this.options = options;
    this.animationState = '*';
  }

  // the purpose of this is to manually force the animation to start and hence
  // to have the snackbar close..
  animateClose(): void {
    this.animationState = 'void';
    clearTimeout(this.durationTimeoutId);
  }

  /**
   * This is called after the animation is done by Angular
   * The state decides whether the component should be destroyed or not
   */
  animationDone(): void {
    if (this.animationState === 'void') {
      this.onDestroy.next();
    } else if (this.animationState === '*') {
      if (this.options) {
        this.dismissAfter(this.options.duration);
      }
    }
  }

  private dismissAfter(duration: number): void {
    if (duration && duration > 0) {
      this.durationTimeoutId = setTimeout(() => this.animateClose(), duration);
    }
  }

}
