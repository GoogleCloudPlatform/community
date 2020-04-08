package main

import (
	"archiver"
	"fmt"
)

func main() {
	fmt.Println("starting")
	ct, _ := archiver.ArchiveTopic()
	fmt.Printf("archived %v messages\n", ct)
	fmt.Println("Finished")
}
