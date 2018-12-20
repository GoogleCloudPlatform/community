package main

import (
	"bytes"
	"context"
	"encoding/base64"
	"encoding/json"
	"flag"
	"fmt"
	"log"
	"math/rand"
	"time"

	"cloud.google.com/go/pubsub"
)

// gcloud beta pubsub topics create mydata
// gcloud beta pubsub subscriptions create --topic mydata testsub
// gcloud beta pubsub subscriptions pull --auto-ack --max-messages 10 testsub

func xrandom(min, max int) int {
	rand.Seed(time.Now().Unix())
	v := rand.Intn(max-min) + min
	return v
}

type msg struct {
	Data   map[string]float64
	Labels map[string]string
}

func newMsg() *msg {
	m := new(msg)
	m.Data = map[string]float64{"voltage": 5.0, "kwh": 7.0}
	m.Labels = make(map[string]string)
	now := time.Now()
	m.Labels["timestamp"] = now.Format(time.RFC3339Nano)
	// attributes["farm"] = farm
	// attributes["location"] = location
	return m
}

func x_main() {
	topicname := flag.String("topic", "mydata", "short topic name")
	// TODO get project from env
	project := flag.String("project", "lyon-iot", "project id")
	flag.Parse()
	ctx := context.Background()
	client, err := pubsub.NewClient(ctx, *project)
	if err != nil {
		log.Fatalf("Could not create pubsub Client: %v", err)
	}
	topic := client.Topic(*topicname)
	topic.PublishSettings = pubsub.PublishSettings{
		NumGoroutines: 10,
	}
	buf := new(bytes.Buffer)
	b64enc := base64.NewEncoder(base64.StdEncoding, buf)
	jsonenc := json.NewEncoder(b64enc)
	locations := []string{"Boston", "Miami", "Chicago"}
	floors := []int{1, 2, 3, 4, 5, 6}
	locationWeights := map[string]float64{
		"Boston":  0.9,
		"Miami":   1.0,
		"Chicago": 1.2,
	}

	for {
		now := time.Now()
		location := locations[rand.Intn(len(locations))]
		floor := floors[rand.Intn(len(floors))]
		locationWeight := locationWeights[location]
		// the kwh will grow every hour
		_, min, _ := now.Clock()
		buf.Reset()
		voltageVal := float64(random(5, 15))
		kwhVal := float64(random(min, min+5))
		m := newMsg()

		fmt.Println(voltageVal, kwhVal)
		fmt.Println(locationWeight)
		m.Data["voltage"] = locationWeight * voltageVal
		m.Data["kwh"] = locationWeight * kwhVal
		fmt.Printf("%v\n", m.Data)
		m.Labels["location"] = location
		m.Labels["floor"] = string(floor)
		jsonenc.Encode(&m)
		// close is required to flush partial blocks of data
		b64enc.Close()
		fmt.Println(buf.String())
		// TODO sort out how to get labels from payload and or subtopic
		// note that for non-iot can use attributes
		attributes := make(map[string]string)
		attributes["deviceId"] = fmt.Sprintf("%s-meter", location)
		attributes["projectId"] = "dummy project id"
		// deviceNumId
		//deviceRegistryLocation
		// deviceRegistryId
		// subfolder
		// msg := &pubsub.Message{Data: buf.Bytes(), Attributes: attributes}

		// TODO error handle
		pubsubPayload, err := json.Marshal(m)
		if err != nil {
			log.Fatal("can not marshall json")
		}
		msg := &pubsub.Message{Data: pubsubPayload, Attributes: attributes}
		result := topic.Publish(ctx, msg)
		id, err := result.Get(ctx)
		if err != nil {
			log.Println(err)
		}
		fmt.Printf("Published a message; msg ID: %v\n", id)
		time.Sleep(500 * time.Millisecond)
	}

}
