import { Injectable } from '@angular/core';
import { Overlay, OverlayRef } from '@angular/cdk/overlay';
import { SpinnerComponent } from '../app/components/spinner/spinner.component';
import { SpinnerOptions } from '../app/components/spinner/spinner-options';
import { ComponentPortal } from '@angular/cdk/portal';

@Injectable()
export class OverlaySpinnerService {

  private spinnerComponent: SpinnerComponent;
  private overlayRef: OverlayRef;
  private readonly DEFAULT_OPTIONS: SpinnerOptions = {
    closable: false,
    duration: 2000
  };

  constructor(private overlay: Overlay) {
    this.overlayRef = this.overlay.create({
      hasBackdrop: true,
      scrollStrategy: this.overlay.scrollStrategies.noop(),
      positionStrategy: this.overlay.position().global().centerHorizontally().centerVertically()
    });
  }

  openSpinner(options?: Partial<SpinnerOptions>): void {
    if (this.overlayRef.hasAttached()) {
      this.overlayRef.detach();
    }

    const portal = new ComponentPortal(SpinnerComponent);
    const componentRef = this.overlayRef.attach(portal);

    this.spinnerComponent = componentRef.instance;
    this.spinnerComponent.open({ ...this.DEFAULT_OPTIONS, ...options});
  }

  closeSpinner(): void {
    setTimeout(() => this.overlayRef.detach(), this.DEFAULT_OPTIONS.duration);
  }

}
