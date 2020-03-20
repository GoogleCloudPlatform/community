package main

import (
	"bufio"
	"context"
	"encoding/csv"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"log"
	"math/rand"
	"os"
	"strconv"
	"strings"
	"time"

	"cloud.google.com/go/pubsub"
)

func getProject() (projectID string) {
	var exists bool
	envCandidates := []string{
		"GCP_PROJECT",
		"GOOGLE_CLOUD_PROJECT",
		"GCLOUD_PROJECT",
	}
	for _, e := range envCandidates {
		projectID, exists = os.LookupEnv(e)
		if exists {
			return projectID
		}
	}
	if !exists {
		log.Fatalf("Set project ID via one of the supported env variables.")
	}
	return ""
}

type deviceMessage struct {
	// a UUID
	DeviceID  string `json:"device_id"`
	Timestamp string `json:"timestamp"`
	// x, y, z
	Orientation map[string]float64 `json:"orientation"`
	LightLevel  int                `json:"light_level"`
	// 0-100
	Temperature   float64 `json:"temperature"`
	ButtonPressed bool    `json:"button_pressed"`
	City          string  `json:"city"`
	// used as group-by key in dataflow
	Region  string  `json:"region"`
	Lat     float64 `json:"lat"`
	Long    float64 `json:"long"`
	Bulkout string  `json:"longstr"`
}

type deviceInfo struct {
	DeviceID string  `json:"device_id"`
	City     string  `json:"city"`
	Region   string  `json:"region"`
	Lat      float64 `json:"lat"`
	Long     float64 `json:"long"`
}

func random(min, max int) int {
	v := rand.Intn(max-min) + min
	return v
}

func getIDs(generate bool, ct int) []*deviceInfo {
	deviceIds := make([]*deviceInfo, 0)

	f, err := os.Open("cities.csv")
	if err != nil {
		log.Fatalln("cities file not found")
	}

	r := csv.NewReader(bufio.NewReader(f))
	for {
		record, err := r.Read()
		// Stop at EOF.
		if err == io.EOF {
			break
		}
		d := &deviceInfo{
			DeviceID: strings.Split(record[0], "=")[1],
			City:     record[2],
			Region:   record[6],
		}
		d.Lat, _ = strconv.ParseFloat(record[4], 64)
		d.Long, _ = strconv.ParseFloat(record[5], 64)
		deviceIds = append(deviceIds, d)

	}

	deviceIds = deviceIds[:ct]
	return deviceIds
}

func main() {

	rand.Seed(time.Now().Unix())

	var bulkString string
	var generateIDs bool = true
	var numDevices int
	var frequency float64
	var device *deviceInfo
	// bulkLen := 20000
	bulkLen := 2000

	fmt.Println("bulking out")
	b := make([]byte, bulkLen)
	for i := 0; i < bulkLen; i++ {

		b[i] = byte(rand.Intn(255))
	}
	bulkString = string(b)
	fmt.Println("done bulking out")
	topicname := flag.String("topic", "demo-data", "short topic name")
	project := getProject()
	temp := flag.String("temp", "med", "temperature: low, med, high")
	streaming := flag.Bool("streaming", true, "streaming setup or bulk")
	flag.IntVar(&numDevices, "numDevices", 25, "number of devices to simulate")
	flag.Float64Var(&frequency, "frequency", 1, "frequency in hertz")

	flag.Parse()

	var topic *pubsub.Topic
	var now time.Time

	ctx := context.Background()
	if *streaming {
		client, err := pubsub.NewClient(ctx, project)
		if err != nil {
			log.Fatalf("Could not create pubsub Client: %v", err)
		}
		topic = client.Topic(*topicname)
	}

	deviceIds := getIDs(generateIDs, numDevices)

	for {
		msgs := make([]*pubsub.Message, 0)
		for i := 0; i < len(deviceIds); i++ {
			now = time.Now()

			now = now.Add(time.Duration(random(-200, 200)) * time.Millisecond)
			data := &deviceMessage{}
			device = deviceIds[i]

			// copy device info into each message
			data.DeviceID = device.DeviceID
			data.Lat = device.Lat
			data.Long = device.Long
			data.City = device.City
			data.Region = device.Region
			data.Timestamp = now.Format("2006-01-02T15:04:05.9999Z07:00")
			data.Bulkout = bulkString

			data.Orientation = map[string]float64{
				"x": rand.Float64(),
				"y": rand.Float64(),
				"z": rand.Float64()}
			// voltage level is .9 to 1.8V expressed as millivolts
			data.ButtonPressed = bool(rand.Intn(100) > 50)
			// data.Potentiometer = rand.Intn(100)

			switch *temp {
			case "low":
				data.Temperature = float64(random(0, 15))
			case "med":
				data.Temperature = float64(random(16, 22))
			case "high":
				data.Temperature = float64(random(30, 40))
			}

			switch device.Region {
			case "APAC":
				data.LightLevel = random(900, 1200)
			case "AMER":
				data.LightLevel = random(1200, 1500)
			case "EMEA":
				data.LightLevel = random(1500, 1800)
			}

			group, _ := strconv.ParseInt(string(data.DeviceID[0]), 16, 64)
			switch group % 4 {
			case 0:
				data.LightLevel = int(float64(data.LightLevel) * float64(now.Month()) / 12.0)
				data.Orientation["x"] = data.Orientation["x"] * 0.10
			case 1:
				data.Orientation["x"] = data.Orientation["x"] * 0.60
			case 2:
				data.Orientation["x"] = data.Orientation["x"] * 0.80
			case 3:
				data.ButtonPressed = bool(rand.Intn(100) > 80)
			}

			if *streaming {
				attributes := make(map[string]string)
				attributes["timestamp"] = data.Timestamp

				jsonData, _ := json.Marshal(*data)
				msg := &pubsub.Message{Data: jsonData, Attributes: attributes}
				msgs = append(msgs, msg)
			} else {
				if jsonData, err := json.Marshal(*data); err != nil {
					log.Fatal("json failed")
				} else {
					os.Stdout.Write(jsonData)
				}
			}
		}
		if *streaming {
			for _, msg := range msgs {
				go func() {
					pubresult := topic.Publish(ctx, msg)
					_, err := pubresult.Get(ctx)
					if err != nil {
						log.Println(err)
					}

				}()
			}
			log.Println("Published Batch")
			time.Sleep(time.Duration(1.0/frequency) * time.Second)
		}

	}

}
