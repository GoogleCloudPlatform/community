import Foundation
import PerfectLib
import PerfectHTTP
import PerfectHTTPServer

// Create HTTP server.
let server = HTTPServer()
var routes = Routes()

// Respond to App Engine health check requests
routes.add(method: .get, uri: "/_ah/health", handler: {
    request, response in
    print("GET - /_ah/health route handler...")
    response.setBody(string: "OK")
    response.completed()
})

// Basic GET request
routes.add(method: .get, uri: "/hello", handler: {
    request, response in
    print("GET - /hello route handler...")
    response.setBody(string: "Hello from Swift on Google App Engine flexible environment!")
    response.completed()
})

// Add the routes to the server.
server.addRoutes(routes)

// Set a listen port of 8080
server.serverPort = 8080

do {
    // Launch the HTTP server.
    try server.start()
} catch PerfectError.networkError(let err, let msg) {
    print("Network error thrown: \(err) \(msg)")
}
