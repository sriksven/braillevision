# Android App

BrailleVision includes a native Android wrapper in `android APP/`. The app is built with Capacitor and packages the mobile web experience in an Android WebView. Image upload, camera capture, and results rendering are handled by the web UI, while the Android shell provides native app packaging and permissions.

## Current Configuration

The checked-in Capacitor config is `android APP/capacitor.config.json`.

```json
{
  "appId": "com.sriksven.braillevision",
  "appName": "BrailleVision",
  "webDir": "www",
  "server": {
    "url": "https://sriksven-braillevision.hf.space",
    "cleartext": true
  }
}
```

Important Android settings:

- Package/application id: `com.sriksven.braillevision`
- Display name: `BrailleVision`
- Min SDK: 23
- Compile SDK: 35
- Target SDK: 35
- Gradle wrapper: 8.11.1
- Permissions: `INTERNET`, `CAMERA`, and `RECORD_AUDIO`

The committed `www/index.html` is only a fallback loading page. In normal use, the app loads the deployed backend from `server.url`.

## Prerequisites

Install:

- Node.js and npm
- Android Studio
- Android SDK Platform 35
- A configured emulator or physical Android device with USB debugging enabled

## Install Dependencies

From the Android app directory:

```bash
cd "android APP"
npm install
```

After dependency changes or Capacitor config changes, sync the native project:

```bash
npx cap sync android
```

## Run From Android Studio

1. Open `android APP/android` in Android Studio.
2. Wait for Gradle sync to finish.
3. Select an emulator or connected Android device.
4. Click Run.

The app should open as `BrailleVision` and load the hosted web UI.

## Build A Debug APK

From the native Android project:

```bash
cd "android APP/android"
./gradlew assembleDebug
```

The debug APK is generated under:

```text
android APP/android/app/build/outputs/apk/debug/
```

Install it on a connected device with:

```bash
adb install app/build/outputs/apk/debug/app-debug.apk
```

## Use A Local Backend

For local development, run the Flask backend from the repository root:

```bash
python app/app.py
```

Then edit `android APP/capacitor.config.json` so the app can reach the backend.

For the Android emulator, use:

```json
"server": {
  "url": "http://10.0.2.2:7860",
  "cleartext": true
}
```

For a physical device, use the development machine's LAN IP address:

```json
"server": {
  "url": "http://192.168.x.x:7860",
  "cleartext": true
}
```

After changing the URL, sync and rebuild:

```bash
cd "android APP"
npx cap sync android
```

If using a physical device, make sure the phone and computer are on the same network and that local firewall rules allow inbound traffic on port `7860`.

## Release Notes

For a Play Store or signed distribution build:

1. Create and secure a release keystore outside the repository.
2. Add signing configuration in the Android Gradle project or through Android Studio.
3. Build a release APK or Android App Bundle.
4. Verify the production `server.url` before signing.

Do not commit keystores, passwords, generated APKs, generated AABs, or local Android SDK paths.

## Troubleshooting

- Blank screen: confirm the `server.url` is reachable from the emulator or device.
- Localhost does not work in emulator: use `10.0.2.2` instead of `127.0.0.1`.
- Camera upload fails: check Android camera permission and browser/WebView file chooser behavior.
- Gradle sync fails: install Android SDK Platform 35 and verify Android Studio is using a compatible JDK.
- Hosted app does not load: open `https://sriksven-braillevision.hf.space` in a browser to verify the backend is online.
