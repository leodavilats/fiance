// ignore_for_file: type=lint
import 'package:firebase_core/firebase_core.dart' show FirebaseOptions;
import 'package:flutter/foundation.dart'
    show defaultTargetPlatform, kIsWeb, TargetPlatform;

/// Default [FirebaseOptions] for use with your Firebase apps.
///
/// Example:
/// ```dart
/// import 'firebase_options.dart';
/// // ...
/// await Firebase.initializeApp(
///   options: DefaultFirebaseOptions.currentPlatform,
/// );
/// ```
class DefaultFirebaseOptions {
  static FirebaseOptions get currentPlatform {
    if (kIsWeb) {
      return web;
    }
    switch (defaultTargetPlatform) {
      case TargetPlatform.android:
        return android;
      case TargetPlatform.iOS:
        return ios;
      case TargetPlatform.macOS:
        return macos;
      case TargetPlatform.windows:
        return windows;
      case TargetPlatform.linux:
        throw UnsupportedError(
          'DefaultFirebaseOptions have not been configured for linux - '
          'you can reconfigure this by running the FlutterFire CLI again.',
        );
      default:
        throw UnsupportedError(
          'DefaultFirebaseOptions are not supported for this platform.',
        );
    }
  }

  static const FirebaseOptions web = FirebaseOptions(
    apiKey: 'AIzaSyDZ4ekN9_s-W5qKY5wIqwvB_1i2SWw7DL4',
    appId: '1:113865070204:web:b864b7cc3e8df9a1519bf9',
    messagingSenderId: '113865070204',
    projectId: 'fiance-088500',
    authDomain: 'fiance-088500.firebaseapp.com',
    storageBucket: 'fiance-088500.firebasestorage.app',
    measurementId: 'G-10FPEEDP0Y',
  );

  static const FirebaseOptions android = FirebaseOptions(
    apiKey: 'AIzaSyAqyA22Y1TPxXQE-xlBC-lUH7X7fGGnwmc',
    appId: '1:113865070204:android:0501835c2b39ab6a519bf9',
    messagingSenderId: '113865070204',
    projectId: 'fiance-088500',
    storageBucket: 'fiance-088500.firebasestorage.app',
  );

  static const FirebaseOptions ios = FirebaseOptions(
    apiKey: 'AIzaSyDRxDswCxW_pxWs6np-QV65dS9yXermM5U',
    appId: '1:113865070204:ios:d9be3b0e6819c5a7519bf9',
    messagingSenderId: '113865070204',
    projectId: 'fiance-088500',
    storageBucket: 'fiance-088500.firebasestorage.app',
    iosBundleId: 'com.fiance.fiance',
  );

  static const FirebaseOptions macos = FirebaseOptions(
    apiKey: 'AIzaSyDRxDswCxW_pxWs6np-QV65dS9yXermM5U',
    appId: '1:113865070204:ios:d9be3b0e6819c5a7519bf9',
    messagingSenderId: '113865070204',
    projectId: 'fiance-088500',
    storageBucket: 'fiance-088500.firebasestorage.app',
    iosBundleId: 'com.fiance.fiance',
  );

  static const FirebaseOptions windows = FirebaseOptions(
    apiKey: 'AIzaSyDZ4ekN9_s-W5qKY5wIqwvB_1i2SWw7DL4',
    appId: '1:113865070204:web:0854928940432ce7519bf9',
    messagingSenderId: '113865070204',
    projectId: 'fiance-088500',
    authDomain: 'fiance-088500.firebaseapp.com',
    storageBucket: 'fiance-088500.firebasestorage.app',
    measurementId: 'G-5MKVJ3FJBH',
  );
}
