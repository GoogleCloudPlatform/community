#/******************************************************************************
#* Copyright 2020 Google
#* Licensed under the Apache License, Version 2.0 (the "License");
#* you may not use this file except in compliance with the License.
#* You may obtain a copy of the License at
#*
#*    http://www.apache.org/licenses/LICENSE-2.0
#*
#* Unless required by applicable law or agreed to in writing, software
#* distributed under the License is distributed on an "AS IS" BASIS,
#* WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#* See the License for the specific language governing permissions and
#* limitations under the License.
#*****************************************************************************/
COMPONENT_EMBED_TXTFILES := certs/private_key.pem

ifndef IDF_CI_BUILD
# Print an error if the certificate/key files are missing
$(COMPONENT_PATH)/certs/private_key.pem:
	@echo "Missing PEM file $@. This file identifies the ESP32 to Google Cloud IoT Core for the example, see README for details."
	exit 1
else  # IDF_CI_BUILD
# this case is for the internal Continuous Integration build which
# compiles all examples. Add some dummy certs so the example can
# compile (even though it won't work)
$(COMPONENT_PATH)/certs/private_key.pem:
	echo "Dummy certificate data for continuous integration" > $@
endif
