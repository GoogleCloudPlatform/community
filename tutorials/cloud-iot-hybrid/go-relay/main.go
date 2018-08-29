/*
# Copyright Google Inc. 2018

# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
*/

package main

import (
	"context"
	"fmt"
	"log"
	"os"

	"cloud.google.com/go/compute/metadata"
	"cloud.google.com/go/pubsub"
	MQTT "github.com/eclipse/paho.mqtt.golang"
)

//define a function for the default message handler
var f MQTT.MessageHandler = func(client MQTT.Client, msg MQTT.Message) {
	fmt.Printf("TOPIC: %s\n", msg.Topic())
	fmt.Printf("MSG: %s\n", msg.Payload())
}

func main() {
	//create a ClientOptions struct setting the broker address, clientid, turn
	//off trace output and set the default message handler
	opts := MQTT.NewClientOptions().AddBroker("tcp://on-prem-rabbit:1883")
	opts.SetClientID("go-simple")
	opts.SetUsername("user")
	opts.SetPassword("abc123")
	opts.SetDefaultPublishHandler(f)

	//create and start a client using the above ClientOptions
	c := MQTT.NewClient(opts)
	if token := c.Connect(); token.Wait() && token.Error() != nil {
		panic(token.Error())
	}

	ctx := context.Background()
	var err error
	proj := os.Getenv("GOOGLE_CLOUD_PROJECT")
	if proj == "" {
		proj, err = metadata.ProjectID()
		if err != nil {
			fmt.Fprintf(os.Stderr, "GOOGLE_CLOUD_PROJECT environment variable must be set.\n")
			os.Exit(1)
		}
	}
	client, err := pubsub.NewClient(ctx, proj)
	if err != nil {
		log.Fatalf("Could not create pubsub Client: %v", err)
	}
	sub := client.Subscription("relay")
	// use async pull to get messages from devices
	err = sub.Receive(ctx, func(ctx context.Context, msg *pubsub.Message) {
		fmt.Printf("Got message: %q\n", string(msg.Data))
		fmt.Println(msg.Attributes["subFolder"])
		// publish the message to the corresponding MQTT topic in the target broker
		token := c.Publish(msg.Attributes["subFolder"], 0, false, msg.Data)
		go func(pubsource *pubsub.Message, token MQTT.Token) {
			token.Wait()
			fmt.Printf("confirmed %s\n", "message id")
			msg.Ack()
		}(msg, token)
	})

	if err != nil {
		log.Fatal(err)
	}

	c.Disconnect(250)
}
