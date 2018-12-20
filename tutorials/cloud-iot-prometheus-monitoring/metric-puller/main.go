package main

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"log"
	"net/http"
	"time"

	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promhttp"

	"cloud.google.com/go/pubsub"
)

type Drainer struct {
	context          *context.Context
	SubscriptionName string
	client           *pubsub.Client
	ProjectId        string
	subscription     *pubsub.Subscription
}

type msg struct {
	Data   map[string]float64
	Labels map[string]string
}

var (
	voltageG = prometheus.NewGaugeVec(prometheus.GaugeOpts{
		Name: "main_votage_in_volts",
		Help: "Main System Bus Voltage",
	},
		[]string{"device", "location"},
	)
	kwhC = prometheus.NewCounterVec(
		prometheus.CounterOpts{
			Name: "kwh_total",
			Help: "Count of KWH",
		},
		[]string{"device", "location"},
	)
)

func init() {
	// Metrics have to be registered to be exposed:
	prometheus.MustRegister(voltageG)
	prometheus.MustRegister(kwhC)
}

func newMsg() *msg {
	m := new(msg)
	m.Data = map[string]float64{"voltage": 5.0, "kwh": 7.0}
	m.Labels = make(map[string]string)
	now := time.Now()
	m.Labels["timestamp"] = now.Format(time.RFC3339Nano)
	return m
}

func pullData(project, subscription string) {

	ctx := context.Background()
	client, err := pubsub.NewClient(ctx, project)
	if err != nil {
		log.Fatalf("Could not create pubsub Client: %v", err)
	}

	sub := client.Subscription(subscription)
	err = sub.Receive(ctx, func(ctx context.Context, msg *pubsub.Message) {
		fmt.Printf("Got message: %q\n", string(msg.Data))
		fmt.Println(msg.Attributes["deviceId"])
		decodedMsg := newMsg()
		json.Unmarshal(msg.Data, &decodedMsg)
		voltageG.With(prometheus.Labels{
			"device":   msg.Attributes["deviceId"],
			"location": decodedMsg.Labels["location"],
		}).Set(float64(decodedMsg.Data["voltage"]))

		kwhC.With(prometheus.Labels{
			"device":   msg.Attributes["deviceId"],
			"location": decodedMsg.Labels["location"],
		}).Add(float64(decodedMsg.Data["kwh"]))
		msg.Ack()
	})
	if err != nil {
		log.Fatal(err)
	}

	// it, err := drainer.subscription.Pull(*drainer.context)
	// if err != nil {
	// 	log.Fatal(err)
	// }
	// defer it.Stop()
	// counter := 1
	// for {
	// 	msg, err := it.Next()
	// 	if err == iterator.Done {
	// 		fmt.Println("no messages")
	// 		time.Sleep(3 * time.Second)
	// 	}
	// 	if err != nil {
	// 		log.Fatal(err)
	// 	}
	// 	// fmt.Printf("%d Got message: %q\n", counter, string(msg.Data))
	// 	d := make(map[string]int)
	// 	counter++
	// 	// buf := new(bytes.Buffer)

	// 	// TODO capture error
	// 	// base64.StdEncoding.Decode(bytedata, msg.Data)
	// 	jsn, _ := base64.StdEncoding.DecodeString(string(msg.Data))
	// 	json.Unmarshal(jsn, &d)
	// 	fmt.Println(d)
	// 	lettuceHeight.With(prometheus.Labels{"farm": msg.Attributes["farm"]}).Set(float64(d["lettuce"]))

	// 	appleCount.With(prometheus.Labels{"farm": msg.Attributes["farm"]}).Add(float64(d["apple"]))
	// 	go msg.Done(true)
	// }
}
func main() {
	var project, subscription string
	flag.StringVar(&subscription, "subscription", "metric-pull", "short subscription name")
	flag.StringVar(&project, "project", "lyon-iot", "project id")
	flag.Parse()

	http.Handle("/metrics", promhttp.Handler())
	fmt.Println("-----------")
	go pullData(project, subscription)
	log.Fatal(http.ListenAndServe(":8080", nil))

}
