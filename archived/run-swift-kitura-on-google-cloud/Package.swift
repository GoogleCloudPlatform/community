import PackageDescription

let package = Package(
    name: "KituraGAE",
    targets: [
        Target(name: "KituraGAE", dependencies: [])
    ],
    dependencies: [
        .Package(url: "https://github.com/IBM-Swift/Kitura.git", majorVersion: 1, minor: 7),
        ]
)
