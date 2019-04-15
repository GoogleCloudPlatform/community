package main

import (
	"bufio"
	"encoding/csv"
	"fmt"
	"io"
	"log"
	"math/rand"
	"net/http"
	"os"
	"strconv"
	"time"

	"github.com/prometheus/client_golang/prometheus/promhttp"
)

func random(min, max int) int {
	rand.Seed(time.Now().Unix())
	v := rand.Intn(max-min) + min
	return v
}

func main() {
	var devicesPerCity int
	deviceEnv := os.Getenv("DEVICE_COUNT")
	if deviceEnv == "" {
		devicesPerCity = 10
	} else {
		if s, err := strconv.ParseInt(deviceEnv, 10, 64); err == nil {
			devicesPerCity = int(s)
		} else {
			log.Println("Unable to parse env, using 10 as default")
			devicesPerCity = 10
		}

	}

	// Load a TXT file.
	f, _ := os.Open("US-cities.csv")

	// Create a new reader.
	r := csv.NewReader(bufio.NewReader(f))
	devices := []*Device{}
	metrics := newMetrics()
	for {
		record, err := r.Read()
		// Stop at EOF.
		if err == io.EOF {
			break
		}
		fmt.Println(record)
		for i := 0; i < devicesPerCity; i++ {
			recordCopy := make([]string, len(record))
			copy(recordCopy, record)
			recordCopy[0] = fmt.Sprintf("%s-%d", recordCopy[0], i)
			d := NewDevice(recordCopy, metrics)
			// fmt.Println(d)
			// fmt.Println(d.startTemp)
			devices = append(devices, d)
			// for value := range record {
			// fmt.Printf("  %v\n", record[value])
			// }
			time.Sleep(1 * time.Millisecond)
			go d.Loop()

		}
	}
	http.Handle("/metrics", promhttp.Handler())
	fmt.Println("-----------")
	log.Fatal(http.ListenAndServe(":8080", nil))

}
