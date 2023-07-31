import PackageDescription

let package = Package(
    name: "VaporGAE",
    targets: [
        Target(name: "VaporGAE", dependencies: [])
    ],
    dependencies: [
        .Package(url: "https://github.com/vapor/vapor.git", majorVersion: 1, minor: 1)
    ]
)
