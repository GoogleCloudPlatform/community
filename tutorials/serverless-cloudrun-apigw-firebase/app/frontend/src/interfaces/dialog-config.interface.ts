export interface DialogConfig {
  hasBackdrop?: boolean;
  backdropClass?: string;
  autoFocus?: boolean;
  disableClose?: boolean;
  data?: any;
}

export const DEFAULT_CONFIG: DialogConfig = {
  hasBackdrop: true,
  backdropClass: 'cdk-overlay-dark-backdrop',
  autoFocus: true,
  disableClose: false,
  data: null
};
