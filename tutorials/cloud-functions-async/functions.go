package jobs

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"strings"
	"time"

	"cloud.google.com/go/firestore"
	"cloud.google.com/go/pubsub"
	"github.com/google/uuid"
)

// enum to json note: https://gist.github.com/lummie/7f5c237a17853c031a57277371528e87

var pClient *pubsub.Client
var fClient *firestore.Client

type JobState int

const (
	Created JobState = iota
	Running
	Completed
	Failed
)

type Job struct {
	ID         string    `json:"id"`
	CreateTime time.Time `json:"created-time"`
	DoneTime   time.Time `json:"done-time" firestore:"DoneTime,omitempty"`
	Done       bool
	Result     string
	State      JobState
	Task       map[string]interface{} `json:"-"`
	// can add a requester, source IP etc if needed
}

func init() {
	// setup pubsub
	// setup firestore
	var exists bool
	projectID, exists := os.LookupEnv("GCP_PROJECT")
	if !exists {
		projectID, exists = os.LookupEnv("GOOGLE_CLOUD_PROJECT")
	}
	if !exists {
		log.Fatalf("Set project ID via GCP_PROJECT or GOOGLE_CLOUD_PROJECT env variable.")
	}

	ctx := context.Background()
	var err error

	fClient, err = firestore.NewClient(ctx, projectID)
	if err != nil {
		log.Fatalf("Cannot create Firestore client: %v", err)
	}

	pClient, err = pubsub.NewClient(context.Background(), projectID)
	if err != nil {
		log.Fatalf("Cannot create PubSub Client %v", err)
	}
}

func AddJob(j *Job) (id string, err error) {
	ctx := context.Background()

	_, err = fClient.Collection("jobs").Doc(j.ID).Set(ctx, j)
	if err != nil {
		log.Printf("error writing job: %s", err)
		return "", err
	}

	js, err := json.Marshal(j.Task)
	if err != nil {
		log.Printf("error publishing task: %s", err)
		return "", err
	}

	task := &pubsub.Message{
		Attributes: map[string]string{"job-id": j.ID},
		Data:       js,
	}
	result := pClient.Topic("jobs").Publish(ctx, task)
	// Block until the result is returned and a server-generated
	// ID is returned for the published message.
	msgID, err := result.Get(ctx)
	if err != nil {
		log.Printf("error publishing task: %s", err)
		return "", err
	}
	log.Printf("published msg %v\n", msgID)
	return j.ID, nil
}

func GetJob(id string) (j *Job, err error) {
	dsnap, err := fClient.Collection("jobs").Doc(id).Get(context.Background())
	// TODO need a 404 condition
	if err != nil {
		log.Printf("error getting job: %s", err)
		return nil, err
	}
	err = dsnap.DataTo(&j)
	if err != nil {
		log.Printf("error getting job: %s", err)
		return nil, err
	}
	return j, nil
}

// func getStats() {}
// a status function could return basic stats about duration work is taking: min/max/mean

func Jobs(w http.ResponseWriter, r *http.Request) {
	switch r.Method {

	case http.MethodGet:
		fmt.Println("Get")
		p := strings.Split(r.URL.Path, "/")
		id := p[len(p)-1]
		j, err := GetJob(id)
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		// optionally strip the task out of the returned result
		// j.Task = nil
		js, err := json.Marshal(j)
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}

		w.Header().Set("Content-Type", "application/json")
		w.Write(js)

	case http.MethodPost:
		fmt.Println("Post")
		var m map[string]interface{}
		// optional TODO: simple validation
		// check worktime between 5 and 60
		err := json.NewDecoder(r.Body).Decode(&m)
		if err != nil {
			log.Printf("error parsing application/json: %v", err)
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}
		j := &Job{
			ID:         uuid.New().String(),
			CreateTime: time.Now(),
			Done:       false,
			State:      Created,
			Task:       m,
		}

		_, err = AddJob(j)
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}

		js, err := json.Marshal(j)
		if err != nil {
			http.Error(w, err.Error(), http.StatusInternalServerError)
			return
		}

		w.Header().Set("Content-Type", "application/json")
		w.Write(js)

	}
}
