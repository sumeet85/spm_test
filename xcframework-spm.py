import os
import subprocess
import shutil
import requests

# Configuration
PROJECT_NAME = "Alamofire"
SCHEME_NAME = "Alamofire iOS"
OUTPUT_DIR = "build"
XCFRAMEWORK_NAME = f"{PROJECT_NAME}.xcframework"
ZIP_NAME = f"{XCFRAMEWORK_NAME}.zip"
GITHUB_REPO = "sumeet85/spm_test"  # Update with your GitHub repository
GITHUB_TOKEN = "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"  # Replace with your valid token
RELEASE_TAG = "v1.0.0"
RELEASE_NAME = "Alamofire Release 1.0.0"
RELEASE_BODY = "This is the first release of Alamofire with XCFramework support."

def run_command(command):
    """Run a shell command and print its output."""
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, text=True, capture_output=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        exit(1)
    return result.stdout.strip()

def clean_build_directory():
    """Clean the build directory to avoid conflicts."""
    if os.path.exists(OUTPUT_DIR):
        print(f"Cleaning up the build directory: {OUTPUT_DIR}")
        shutil.rmtree(OUTPUT_DIR)
    os.makedirs(OUTPUT_DIR, exist_ok=True)

def build_xcframework():
    """Build XCFramework for iOS and iOS Simulator."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Build for iOS
    print("Building for iOS...")
    run_command(
        f"xcodebuild archive -scheme '{SCHEME_NAME}' "
        f"-destination 'generic/platform=iOS' "
        f"-archivePath './{OUTPUT_DIR}/{PROJECT_NAME}-iOS.xcarchive' "
        f"SKIP_INSTALL=NO BUILD_LIBRARY_FOR_DISTRIBUTION=YES"
    )

    # Build for iOS Simulator
    print("Building for iOS Simulator...")
    run_command(
        f"xcodebuild archive -scheme '{SCHEME_NAME}' "
        f"-destination 'generic/platform=iOS Simulator' "
        f"-archivePath './{OUTPUT_DIR}/{PROJECT_NAME}-iOS-Simulator.xcarchive' "
        f"SKIP_INSTALL=NO BUILD_LIBRARY_FOR_DISTRIBUTION=YES"
    )

    # Create XCFramework
    print("Creating XCFramework...")
    run_command(
        f"xcodebuild -create-xcframework "
        f"-framework './{OUTPUT_DIR}/{PROJECT_NAME}-iOS.xcarchive/Products/Library/Frameworks/{PROJECT_NAME}.framework' "
        f"-framework './{OUTPUT_DIR}/{PROJECT_NAME}-iOS-Simulator.xcarchive/Products/Library/Frameworks/{PROJECT_NAME}.framework' "
        f"-output './{OUTPUT_DIR}/{XCFRAMEWORK_NAME}'"
    )

def create_zip():
    """Zip the XCFramework."""
    zip_path = os.path.join(OUTPUT_DIR, ZIP_NAME)
    xcframework_path = os.path.join(OUTPUT_DIR, XCFRAMEWORK_NAME)

    if not os.path.exists(xcframework_path):
        print(f"Error: {XCFRAMEWORK_NAME} not found at {xcframework_path}")
        exit(1)

    print(f"Zipping {XCFRAMEWORK_NAME}...")
    shutil.make_archive(xcframework_path, 'zip', OUTPUT_DIR, XCFRAMEWORK_NAME)
    print(f"Created ZIP: {zip_path}")

def calculate_checksum():
    """Calculate checksum for the zip file."""
    print(f"Calculating checksum for {ZIP_NAME}...")
    checksum = run_command(f"swift package compute-checksum ./{OUTPUT_DIR}/{ZIP_NAME}")
    print(f"Checksum: {checksum}")
    return checksum

def upload_to_github():
    """Upload the .zip file to GitHub as a release asset."""
    print("Creating GitHub release...")
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    create_release_url = f"https://api.github.com/repos/{GITHUB_REPO}/releases"

    # Create the release
    response = requests.post(
        create_release_url,
        headers=headers,
        json={
            "tag_name": RELEASE_TAG,
            "name": RELEASE_NAME,
            "body": RELEASE_BODY,
            "draft": False,
            "prerelease": False
        }
    )

    if response.status_code != 201:
        print(f"Error creating release: {response.status_code}, {response.text}")
        exit(1)

    release = response.json()
    upload_url = release["upload_url"].replace("{?name,label}", "")

    # Upload the asset
    print(f"Uploading {ZIP_NAME}...")
    with open(f"./{OUTPUT_DIR}/{ZIP_NAME}", "rb") as file_data:
        headers["Content-Type"] = "application/zip"
        response = requests.post(
            upload_url,
            headers=headers,
            params={"name": ZIP_NAME},
            data=file_data
        )

    if response.status_code != 201:
        print(f"Error uploading asset: {response.status_code}, {response.text}")
        exit(1)

    print("Upload successful!")
    return release["html_url"]

def create_spm_package(checksum):
    """Create a Swift Package Manager package with a binary target."""
    spm_dir = f"{PROJECT_NAME}-SPM"
    if os.path.exists(spm_dir):
        shutil.rmtree(spm_dir)
    os.makedirs(spm_dir, exist_ok=True)

    print("Creating SPM package...")

    package_swift_content = f"""
    // swift-tools-version:5.3
    import PackageDescription

    let package = Package(
        name: "{PROJECT_NAME}",
        platforms: [
            .iOS(.v13)
        ],
        products: [
            .library(
                name: "{PROJECT_NAME}",
                targets: ["{PROJECT_NAME}"]
            ),
        ],
        targets: [
            .binaryTarget(
                name: "{PROJECT_NAME}",
                url: "https://github.com/{GITHUB_REPO}/releases/download/{RELEASE_TAG}/{ZIP_NAME}",
                checksum: "{checksum}"
            ),
        ]
    )
    """

    package_file_path = os.path.join(spm_dir, "Package.swift")
    with open(package_file_path, "w") as file:
        file.write(package_swift_content)

    print(f"SPM package created at {package_file_path}")

def commit_spm_package_to_github(spm_dir):
    """Commit the SPM package to a GitHub repository."""
    print("Committing SPM package to GitHub...")
    os.chdir(spm_dir)
    run_command("git init")
    run_command("git add .")
    run_command("git commit -m 'Add SPM package with binary target'")
    run_command(f"git remote add origin https://github.com/{GITHUB_REPO}.git")
    run_command("git branch -M main")
    run_command("git push -u origin main")
    os.chdir("..")
    print("SPM package committed to GitHub.")

def main():
    print("Starting XCFramework build process...")
    clean_build_directory()
    build_xcframework()
    create_zip()
    checksum = calculate_checksum()
    create_spm_package(checksum)
    release_url = upload_to_github()
    commit_spm_to_github()
    print(f"GitHub release created: {release_url}")
    print(f"Checksum for Package.swift: {checksum}")
    print("Done!")

if __name__ == "__main__":
    main()
