
    // swift-tools-version:5.3
    import PackageDescription

    let package = Package(
        name: "Alamofire",
        platforms: [
            .iOS(.v13)
        ],
        products: [
            .library(
                name: "Alamofire",
                targets: ["Alamofire"]
            ),
        ],
        targets: [
            .binaryTarget(
                name: "Alamofire",
                url: "https://github.com/sumeet85/spm_test/releases/download/v1.0.0/Alamofire.xcframework.zip",
                checksum: "0c1c8b1d41640b45a6d73b8388425196e86f04785071b24a0f72550413a5c028"
            ),
        ]
    )
    