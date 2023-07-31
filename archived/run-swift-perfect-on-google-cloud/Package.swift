import PackageDescription

let package = Package(
    name: "PerfectGAE",
    targets: [
        Target(name: "PerfectGAE", dependencies: [])
    ],
    dependencies: [
        .Package(url: "https://github.com/PerfectlySoft/Perfect-HTTPServer.git",
                 majorVersion: 2, minor: 0)
    ]
)
