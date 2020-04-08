package main

import (
	"context"
	"encoding/json"
	"jobs"
	"log"
	"os"
	"time"

	"cloud.google.com/go/firestore"
	"cloud.google.com/go/pubsub"
)

func main() {
	var exists bool
	projectID, exists := os.LookupEnv("GCP_PROJECT")
	if !exists {
		projectID, exists = os.LookupEnv("GOOGLE_CLOUD_PROJECT")
	}
	if !exists {
		log.Fatalf("Set project ID via GCP_PROJECT or GOOGLE_CLOUD_PROJECT env variable.")
	}

	var err error
	ctx := context.Background()

	pClient, err := pubsub.NewClient(ctx, projectID)
	if err != nil {
		log.Fatalf("Cannot create PubSub Client %v", err)
	}

	fClient, err := firestore.NewClient(ctx, projectID)
	if err != nil {
		log.Fatalf("Cannot create Firestore client: %v", err)
	}

	sub := pClient.Subscription("worker-tasks")
	err = sub.Receive(ctx, func(cctx context.Context, msg *pubsub.Message) {
		defer msg.Ack()
		jobID := msg.Attributes["job-id"]
		log.Printf("Starting on task %v", jobID)
		taskDoc := fClient.Collection("jobs").Doc(jobID)
		var task map[string]interface{}
		var err error
		err = json.Unmarshal(msg.Data, &task)
		if err != nil {
			log.Fatalf("Cannot get task: %v", err)
		}
		update := map[string]interface{}{
			"State": jobs.Running,
		}
		taskDoc.Set(cctx, update, firestore.MergeAll)

		time.Sleep(time.Duration(task["worktime"].(float64)) * time.Second)
		update = map[string]interface{}{
			"DoneTime": time.Now(),
			"Done":     true,
			"Result":   "OK completed",
			"State":    jobs.Completed,
		}
		taskDoc.Set(cctx, update, firestore.MergeAll)
		log.Printf("Finished task %v", jobID)
	})
}
