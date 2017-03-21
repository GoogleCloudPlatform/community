import Foundation
import Vapor

let drop = Droplet()

// Respond to GAE health check requests
drop.get("/_ah/health") { request in
    print("GET - /_ah/health route handler...")
    return "OK"
}

// Basic GET request
drop.get("/hello") { request in
    print("GET - /hello route handler...")
    return "Hello from Vapor on GAE!"
}

// Start server on 8080 (default)
drop.run()
