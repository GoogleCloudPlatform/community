import Foundation
import Vapor

let drop = Droplet()

// Respond to GAE health check requests
drop.get("/_ah/health") { request in
    print("ALL - /_ah/health route handler...")
    return "OK"
}

// Basic GET request
drop.get("/hello") { request in
    print("GET - /hello route handler...")
    return "Hello from Swift on GAE Flex!!"
}

// Start server on 8080 (default)
drop.run()
