package main

import (
	"fmt"
	"jobs"
	"log"
	"time"

	"github.com/google/uuid"
)

func main() {
	fmt.Println("Post Test")
	m := map[string]interface{}{"worktime": 10}
	// simple validation
	// check worktime between 5 and 60
	j := &jobs.Job{
		ID:         uuid.New().String(),
		CreateTime: time.Now(),
		DoneTime:   time.Time{},
		Done:       false,
		State:      jobs.Created,
		Task:       m,
	}

	_, err := jobs.AddJob(j)
	if err != nil {
		log.Fatalf("Cannot create job: %v", err)
	}
}
