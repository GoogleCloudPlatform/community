package main

import (
	"fmt"
	"hash/fnv"
	"math"
	"regexp"
	"strconv"
	"strings"
	"time"

	"github.com/prometheus/client_golang/prometheus"
	"golang.org/x/exp/rand"
	"gonum.org/v1/gonum/stat/distuv"
)

func getStartTime() time.Time {
	minUp := &distuv.Normal{
		Mu:    8000,
		Sigma: 1000,
		Src:   rand.NewSource(uint64(time.Now().UTC().UnixNano())),
	}
	return time.Now().Add(time.Duration(minUp.Rand()*-1) * time.Minute)
}

func hash(s string) uint32 {
	h := fnv.New32a()
	h.Write([]byte(s))
	return h.Sum32()
}

func getFW(cityname string) (fw string) {
	firmwareVersions := []string{"v1.0", "v1.2a", "v1.1", "v0.9LTS"}
	fw = firmwareVersions[int(hash(cityname))%len(firmwareVersions)]
	return
}

func getHW(cityname string) (fw string) {
	firmwareVersions := []string{"rev1", "rev2", "rev3", "rev4.proto"}
	fw = firmwareVersions[int(hash(cityname))%len(firmwareVersions)]
	return
}

type metricsHolder struct {
	msgCounter     *prometheus.CounterVec
	startTimeGauge *prometheus.GaugeVec
	Temp           *prometheus.GaugeVec
	// pubLatency     *prometheus.HistogramVec
	// increase with distance?
	info  *prometheus.GaugeVec
	Light *prometheus.GaugeVec
	// find anomaly - holt-winters?
	// instant value that is greater than some delta from smoothed value

	ButtonCount *prometheus.CounterVec
	// button counter
	// region segmentation?
	// battery

	LidOpen               *prometheus.GaugeVec
	LidOpenStart          *prometheus.GaugeVec
	LidOpenDuration       *prometheus.HistogramVec
	ackDurationsHistogram *prometheus.HistogramVec
}

func newMetrics() (mh *metricsHolder) {
	labels := []string{"region", "instance", "firmware", "hardware"}

	mh = &metricsHolder{}

	mh.ackDurationsHistogram = prometheus.NewHistogramVec(prometheus.HistogramOpts{
		Name:    "mqtt_telemetry_puback_latency",
		Help:    "MQTT ack latency distributions.",
		Buckets: prometheus.LinearBuckets(50, 20, 20),
	}, []string{"instance"})

	mh.info = prometheus.NewGaugeVec(prometheus.GaugeOpts{
		Name: "device_info",
		Help: "common info-block labels",
	},
		labels,
	)

	mh.startTimeGauge = prometheus.NewGaugeVec(prometheus.GaugeOpts{
		Name: "device_boot_time",
		Help: "timestamp of device boot",
	},
		[]string{"instance"},
	)

	mh.Temp = prometheus.NewGaugeVec(prometheus.GaugeOpts{
		Name: "room_external_temp",
		Help: "temp outside housing celcius",
	},
		[]string{"instance"},
	)

	mh.Light = prometheus.NewGaugeVec(prometheus.GaugeOpts{
		Name: "room_luminance",
		Help: "room temperature",
	},
		[]string{"instance"},
	)

	mh.msgCounter = prometheus.NewCounterVec(prometheus.CounterOpts{
		Name: "device_msgs_total",
		Help: "count of messages by device",
	},
		[]string{"instance"},
	)

	mh.ButtonCount = prometheus.NewCounterVec(prometheus.CounterOpts{
		Name: "action_button_counter",
		Help: "count of presses of button 'action'",
	},
		[]string{"instance"},
	)

	mh.LidOpen = prometheus.NewGaugeVec(prometheus.GaugeOpts{
		Name: "lid_open_status",
		Help: "lid open or closed",
	},
		[]string{"instance"},
	)

	mh.LidOpenStart = prometheus.NewGaugeVec(prometheus.GaugeOpts{
		Name: "lid_open_start_time",
		Help: "Time lid was last opened",
	},
		[]string{"instance"},
	)

	mh.LidOpenDuration = prometheus.NewHistogramVec(prometheus.HistogramOpts{
		Name: "lid_open_duration_seconds",
		Help: "duration lid is open",
		// 10 buckets exponential buckets
		Buckets: prometheus.ExponentialBuckets(30, 1.8, 10),
	},
		[]string{"instance"},
	)
	// TODO east vs west

	prometheus.MustRegister(
		mh.info,
		mh.msgCounter,
		mh.startTimeGauge,
		mh.Temp,
		mh.Light,
		mh.ButtonCount,
		mh.LidOpen,
		mh.LidOpenDuration,
		mh.LidOpenStart,
		mh.ackDurationsHistogram,
	)
	return mh
}

type Device struct {
	StartTime   time.Time
	ID          string
	FW          string
	HW          string
	City        string
	State       string
	Lat         float64
	Long        float64
	Population  int64
	doorOpen    bool
	startTemp   float64
	metrics     *metricsHolder
	lidOpen     bool
	lidOpenTime time.Time
}

func getLat(latString string) (float64, error) {
	latExtract := regexp.MustCompile(`(\ [\d.]+)`)
	latMatch := latExtract.FindStringSubmatch(latString)
	lat := latMatch[0]
	return strconv.ParseFloat(lat, 64)
}

func NewDevice(city []string, metrics *metricsHolder) *Device {
	d := &Device{metrics: metrics}
	// TODO perhaps make this a little less obvious
	d.ID = strings.ToLower(strings.Replace(city[0], " ", "", -1))
	// set a boot time for the device
	d.StartTime = getStartTime()
	d.City = city[0]
	d.State = city[1]
	d.Lat, _ = getLat(city[5])
	d.Population, _ = strconv.ParseInt(strings.Replace(city[2], ",", "", -1), 10, 64)
	d.FW = getFW(d.City)
	d.HW = getHW(d.City)
	d.startTemp = distuv.Normal{
		Mu:    25,
		Sigma: 2,
		Src:   rand.NewSource(uint64(time.Now().UTC().UnixNano())),
	}.Rand()
	// set common information with info-block

	d.metrics.startTimeGauge.WithLabelValues(d.ID).Set(float64(d.StartTime.Unix()))
	d.metrics.info.WithLabelValues(d.State, d.ID, d.FW, d.HW).Set(1)
	d.metrics.Temp.WithLabelValues(d.ID).Set(d.startTemp)
	d.lidOpen = false
	return d
}

func (d *Device) Loop() {
	t := time.Now()
	for {
		t = time.Now()
		d.metrics.msgCounter.WithLabelValues(d.ID).Inc()
		// lat values are 70-120, max sim latency ~300ms
		simLatency := (((((d.Lat - 70) * 2) / 100) * 300) + (rand.Float64() * 10.0))
		d.metrics.ackDurationsHistogram.WithLabelValues(d.ID).Observe(simLatency)
		newTempVariance := rand.Float64() * 2.0
		if rand.Intn(1) == 1 {
			//coin toss as to whether temp increasing or decreasing
			newTempVariance = newTempVariance * -1
		}
		reboot := &distuv.Normal{
			Mu:    10,
			Sigma: 2,
			Src:   rand.NewSource(uint64(time.Now().UTC().UnixNano())),
		}
		var rebootTime time.Duration
		rebootTime = time.Duration(reboot.Rand()) * time.Minute
		if d.ID == "boston-5" {
			// defective device - keeps rebooting
			rebootTime = time.Duration(20 * time.Second)
		}
		if d.StartTime.Add(rebootTime).Before(time.Now()) {
			// simulated reboot
			d.StartTime = time.Now()
			d.metrics.startTimeGauge.WithLabelValues(d.ID).Set(float64(d.StartTime.Unix()))
		}
		d.metrics.Temp.WithLabelValues(d.ID).Set(d.startTemp + newTempVariance)

		// light behavior
		// light gets brightest at the 30 minute mark - peaks at a value of .85
		l := rand.Float64()/10 + (1 - (math.Abs(float64(t.Minute()-30))/30)*0.85)
		// fmt.Println((1 - (math.Abs(float64(t.Minute()-30))/30)*0.85))
		// fmt.Println(newTempVariance)
		// fmt.Println(l)
		fmt.Printf(d.ID)
		fmt.Println("----")
		d.metrics.Light.WithLabelValues(d.ID).Set(l)

		if d.lidOpen == true {
			if rand.Float64() > 0.85 {
				fmt.Println("Lid Closing")
				// 15% chance of closing it
				d.lidOpen = false
				d.metrics.LidOpen.WithLabelValues(d.ID).Set(0)
				d.metrics.LidOpenDuration.WithLabelValues(d.ID).Observe(time.Since(d.lidOpenTime).Seconds())
			}

		} else {
			if rand.Float64() > 0.95 {
				fmt.Println("Lid Opening")
				// 5% chance lid should open this loop
				d.lidOpen = true
				d.lidOpenTime = time.Now()
				d.metrics.LidOpenStart.WithLabelValues(d.ID).Set(float64(d.lidOpenTime.Unix()))
				d.metrics.LidOpen.WithLabelValues(d.ID).Set(1.0)
			}
		}

		time.Sleep(time.Duration(random(57000, 68000)) * time.Millisecond)
	}

}
