@Override
public void onClick(View v) {
   int i = v.getId();
   if (i == R.id.button_camera) {
       launchCamera();
   } else if (i == R.id.button_sign_in) {
       signInAnonymously();
   } else if (i == R.id.button_detections) {
       retrieveMetadata();
       updateUI(mAuth.getCurrentUser());
   }
}
