package archiver

import (
	"context"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"os"
	"sync"
	"time"

	"cloud.google.com/go/pubsub"
	"cloud.google.com/go/storage"
)

var projectID string

var pClient *pubsub.Client
var sClient *storage.Client
var b *storage.BucketHandle
var sub *pubsub.Subscription
var timeout = 5 * time.Second

// set the maximum bytes to write to a GCS file object
var maxBytes = 1 * 1024 * 1024
var ob *storage.Writer
var msgsToAck = []*pubsub.Message{}
var cFunc context.CancelFunc
var path string
var bytes = 0

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

func init() {
	// err is pre-declared to avoid shadowing client.
	var err error

	sClient, err = storage.NewClient(context.Background())
	if err != nil {
		log.Fatalf("storage.NewClient: %v", err)
	}

	bucketName, exists := os.LookupEnv("BUCKET_NAME")
	if !exists {
		bucketName = "ptone-serverless.appspot.com"
	}

	b = sClient.Bucket(bucketName)

	projectID = getProject()

	pClient, err = pubsub.NewClient(context.Background(), projectID)
	if err != nil {
		log.Fatalf("Cannot create PubSub Client %v", err)
	}
	subName, exists := os.LookupEnv("SUBSCRIPTION_NAME")
	if !exists {
		subName = "bulk-drainer"
	}
	sub = pClient.Subscription(subName)
	sub.ReceiveSettings.NumGoroutines = 1
	// this needs to be a number large enough to accomodate your file/archive/chunk size
	sub.ReceiveSettings.MaxOutstandingMessages = 10000
}

// The cleanup function, closes the currently written object
// and acknowledges written pubsub messages
func cleanup() {
	if ob == nil {
		// writer was never set, no msgs received
		return
	}
	err := ob.Close()
	if err != nil {
		log.Println(err)
		for _, m := range msgsToAck {
			m.Nack()
		}
	} else {
		for _, m := range msgsToAck {
			m.Ack()
		}
	}
	msgsToAck = []*pubsub.Message{}
	bytes = 0
	ob = nil
}

func cleanupAndCancel() {
	cleanup()
	log.Println("cancel rec")
	cFunc()
}

type PubSubMessage struct {
	Data []byte `json:"data"`
}

// ArchiveTopic drains messages from Cloud Pub/Sub into a bucket
func ArchiveTopic() (ct int, err error) {
	log.Println("Starting Archive")
	var cctx context.Context
	cctx, cFunc = context.WithCancel(context.Background())
	defer cFunc()
	timer := time.AfterFunc(timeout, cleanupAndCancel)
	var mu sync.Mutex
	received := 0
	bytes = 0
	log.Println("start receive")
	err = sub.Receive(cctx, func(ctx context.Context, msg *pubsub.Message) {
		mu.Lock()
		defer mu.Unlock()
		if ob == nil {
			now := time.Now()
			// store this chunk of data into a bucket following a date-convention path
			path = now.Format("2006/01/02/15_04_05.999")
			log.Println("starting new file", path)
			ob = b.Object(path).NewWriter(ctx)
		}

		bytes += len(msg.Data)
		if _, err := ob.Write(msg.Data); err != nil {
			log.Fatal("Failed to write to temporary file", err)
		}
		ob.Write([]byte("\n"))
		msgsToAck = append(msgsToAck, msg)
		received++
		if cctx.Err() == nil {
			timer.Reset(timeout)
		}
		if bytes > maxBytes {
			log.Println("Done with batch")
			cleanup()
		}
	})
	if err != nil {
		// receive error
		log.Println(err)
	}
	if received == 0 {
		log.Println("Removing empty ob")
		b.Object(path).Delete(context.Background())
	}
	return received, nil
}

// Archiver Cloud Function that initiates the archive task work
func Archiver(ctx context.Context, m PubSubMessage) error {
	start := time.Now()
	received, err := ArchiveTopic()
	elapsed := time.Since(start)
	log.Printf("Archiving took %s", elapsed)
	if err != nil {
		log.Println("Error: ", err)
	} else {
		log.Printf("processed %v messages", received)
	}
	return err
}

// StackDriverRelay durably records the stackdriver event from a http webhook to pubsub message
func StackDriverRelay(w http.ResponseWriter, r *http.Request) {
	keys, ok := r.URL.Query()["token"]

	if !ok || len(keys[0]) < 1 {
		log.Println("Url Param 'key' is missing")
		http.Error(w, "Unauthorized.", http.StatusUnauthorized)
		return
	}
	var expectedToken string
	expectedToken, exists := os.LookupEnv("AUTH_TOKEN")
	if !exists {
		expectedToken = "abcd"
	}
	token := keys[0]
	if token != expectedToken {
		log.Println("Invalid Token")
		http.Error(w, "Unauthorized.", http.StatusUnauthorized)
		return
	}
	// TODO get incident details into message
	ctx := context.Background()
	payload, err := ioutil.ReadAll(r.Body)
	if err != nil {
		log.Println("error with request body", err)
		http.Error(w, "error with request body", http.StatusBadRequest)
		return
	}
	// the topic 'drain-tasks' is a hard coded system-level topic in this case
	_, err = pClient.Topic("drain-tasks").Publish(ctx, &pubsub.Message{Data: payload}).Get(ctx)

	if err != nil {
		log.Println("error publishing", err)
		http.Error(w, "error publishing", http.StatusInternalServerError)
		return
	}
	fmt.Fprint(w, "ok")

}
