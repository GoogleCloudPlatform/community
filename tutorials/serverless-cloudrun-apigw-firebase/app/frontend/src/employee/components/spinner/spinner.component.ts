import {ChangeDetectionStrategy, Component, OnInit} from '@angular/core';
import {SpinnerOptions} from './spinner-options';

@Component({
  selector: 'app-spinner',
  changeDetection: ChangeDetectionStrategy.OnPush,
  templateUrl: './spinner.component.html',
  styleUrls: ['./spinner.component.scss']
})
export class SpinnerComponent implements OnInit {

  options: SpinnerOptions;

  open(options: SpinnerOptions): void {
    this.options = options;
  }

  constructor() { }

  ngOnInit(): void {
  }

}
