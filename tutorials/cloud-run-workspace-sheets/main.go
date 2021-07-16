package main

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"os"
	"text/template"

	"google.golang.org/api/sheets/v4"
)

var sheetsAPI *sheets.Service
var tmpl *template.Template

// Prints the names and majors of students in a sample spreadsheet:
// https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit
const spreadsheetId = "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms"

func getSheetData() (data [][]interface{}, err error) {
	readRange := "Class Data!A2:E"
	resp, err := sheetsAPI.Spreadsheets.Values.Get(spreadsheetId, readRange).Do()
	if err != nil {
		return nil, err
	}

	if len(resp.Values) == 0 {
		fmt.Println("No data found.")
	}
	return resp.Values, nil
}

func handler(w http.ResponseWriter, r *http.Request) {
	data, err := getSheetData()
	if err != nil {
		log.Printf("Unable to get data: %v", err)
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	tmpl.Execute(w, data)
}

func main() {
	ctx := context.Background()
	var err error

	// Get the layout template:
	tmpl, err = template.ParseFiles("layout.html")
	if err != nil {
		log.Fatalf("Unable to get template: %v", err)
	}

	// Use Default credentials
	sheetsAPI, err = sheets.NewService(ctx)
	if err != nil {
		log.Fatalf("Unable to get sheets client: %v", err)
	}

	http.HandleFunc("/", handler)

	// Determine port for HTTP service.
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
		log.Printf("defaulting to port %s", port)
	}

	// Start HTTP server.
	log.Printf("listening on port %s", port)
	if err := http.ListenAndServe(":"+port, nil); err != nil {
		log.Fatal(err)
	}
}
