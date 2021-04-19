import Foundation
import Kitura

let router = Router()

// Respond to App Engine health check requests
router.all("/_ah/health") { request, response, _ in
    print("ALL - /_ah/health route handler...")
    try response.send("OK").end()
}

// Basic GET request
router.get("/hello") { request, response, _ in
    print("GET - /hello route handler...")
    try response.status(.OK).send("Hello from Swift on Google App Engine flexible environment!").end()
}

// Start server on 8080
Kitura.addHTTPServer(onPort: 8080, with: router)
Kitura.run()
