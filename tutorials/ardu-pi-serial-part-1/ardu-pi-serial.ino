/*
Copyright 2018 Google LLC. All rights reserved. Licensed under the Apache License, Version 2.0 (the “License”); you may not use this file except in compliance with the License. You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an “AS IS” BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

Any software provided by Google hereunder is distributed “AS IS”, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, and is not intended for production use.
*/

#define WINDGEN_PIN A0
#define SOLARGEN_PIN A1

int windgen = 0;
int solargen = 0;
char sendBuffer[32];
char ch = 0;

void setup() {
  Serial.begin(115200);
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, LOW);
}

void loop(){
  if (Serial.available()) {
     ch = Serial.read();
     if (ch == '0') {
       sendTelemetry();
     }
  }
}

void sendTelemetry() {
  digitalWrite(LED_BUILTIN, HIGH);
  memset(sendBuffer, 0, sizeof(sendBuffer));
  int windgen = analogRead(WINDGEN_PIN);
  int solargen = analogRead(SOLARGEN_PIN);
  sprintf(sendBuffer, "S s:%d w:%d", solargen, windgen);
  Serial.println(sendBuffer);
  digitalWrite(LED_BUILTIN, LOW);
}
