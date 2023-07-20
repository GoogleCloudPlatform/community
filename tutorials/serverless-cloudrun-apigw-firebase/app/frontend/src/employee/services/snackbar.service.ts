import { Injectable } from '@angular/core';
import { Overlay, OverlayRef } from '@angular/cdk/overlay';
import { ComponentPortal } from '@angular/cdk/portal';
import { SnackbarComponent } from '../components';
import { SnackbarOptions } from '../components/snackbar/snackbar-options';

@Injectable()
export class SnackbarService {

  private overlayRef: OverlayRef;
  private snackbarComp: SnackbarComponent;
  private readonly CORNER_OFFSET = '20px';
  private readonly DEFAULT_OPTIONS: SnackbarOptions = {
    severity: 'info',
    closable: true,
    duration: 5000
  };

  constructor(private overlay: Overlay) {
    this.overlayRef = this.overlay.create({
      hasBackdrop: false,
      scrollStrategy: this.overlay.scrollStrategies.noop(),
      positionStrategy: this.overlay.position()
      .global()
      .right(this.CORNER_OFFSET)
      .bottom(this.CORNER_OFFSET)
    });
  }

  openSnackbar(message: string, options?: Partial<SnackbarOptions>): void {
    if (this.overlayRef.hasAttached()) {
      this.overlayRef.detach();
    }

    const portal = new ComponentPortal(SnackbarComponent);
    const componentRef = this.overlayRef.attach(portal);

    this.snackbarComp = componentRef.instance;
    this.snackbarComp.open(message, { ...this.DEFAULT_OPTIONS, ...options});
  }
}
