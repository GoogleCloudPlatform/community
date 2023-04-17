/*
 * Copyright 2023 Google Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *   http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package main

import (
	"os"

	"github.com/GoogleCloudPlatform/community/tutorials/dataflow-beam-golang-sdk/pubsubbq"
)

func main() {
	projectId := os.Getenv("PROJECT_ID")
	pubsub_topic := os.Getenv("PUBSUB_TOPIC")
	pubsub_subscription := os.Getenv("PUBSUB_SUBSCRIPTION")
	bq_table_string := os.Getenv("BQ_TABLE_STRING")

	pubsubbq.PubsubToBigQuery(projectId, pubsub_topic, pubsub_subscription, bq_table_string)
}
