import java.util.Properties

plugins {
    id("com.android.application")
    id("kotlin-android")
    // The Flutter Gradle Plugin must be applied after the Android and Kotlin Gradle plugins.
    id("dev.flutter.flutter-gradle-plugin")
    id("com.google.gms.google-services")
}

// A chave de release mora em android/key.properties, fora do git (ver README).
// Sem ela o build cai na chave de debug, que a Play Store recusa — e avisa em voz alta.
val chaveDeRelease =
    Properties().apply {
        val arquivo = rootProject.file("key.properties")
        if (arquivo.exists()) arquivo.inputStream().use { load(it) }
    }

val campoDaChave: (String) -> String = { campo ->
    val valor = chaveDeRelease.getProperty(campo)
    require(!valor.isNullOrBlank()) { "android/key.properties existe mas nao declara $campo" }
    valor
}

android {
    namespace = "com.fiance.fiance"
    compileSdk = flutter.compileSdkVersion
    ndkVersion = flutter.ndkVersion

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
        // Exigido por flutter_local_notifications.
        isCoreLibraryDesugaringEnabled = true
    }

    kotlinOptions {
        jvmTarget = JavaVersion.VERSION_17.toString()
    }

    defaultConfig {
        // TODO: Specify your own unique Application ID (https://developer.android.com/studio/build/application-id.html).
        applicationId = "com.fiance.fiance"
        // You can update the following values to match your application needs.
        // For more information, see: https://flutter.dev/to/review-gradle-config.
        // minSdk 23 é exigido pelo firebase_messaging.
        minSdk = maxOf(flutter.minSdkVersion, 23)
        targetSdk = flutter.targetSdkVersion
        versionCode = flutter.versionCode
        versionName = flutter.versionName
    }

    signingConfigs {
        if (!chaveDeRelease.isEmpty) {
            create("release") {
                val arquivo = rootProject.file(campoDaChave("storeFile"))
                require(arquivo.exists()) { "keystore declarado em key.properties nao existe: $arquivo" }
                storeFile = arquivo
                storePassword = campoDaChave("storePassword")
                keyAlias = campoDaChave("keyAlias")
                keyPassword = campoDaChave("keyPassword")
            }
        }
    }

    buildTypes {
        release {
            signingConfig = signingConfigs.findByName("release") ?: signingConfigs.getByName("debug")
        }
    }
}

// O APK de release pode sair com a chave de debug — serve para rodar no aparelho, e o
// `flutter build apk` engole o aviso do Gradle. O App Bundle e o artefato de loja: sem chave
// de verdade ele nao sai, porque um .aab assinado em debug e recusado la na ponta.
val temChaveDeRelease = !chaveDeRelease.isEmpty

tasks.matching { it.name.startsWith("bundle") && it.name.endsWith("Release") }.configureEach {
    doFirst {
        check(temChaveDeRelease) {
            "App Bundle de release exige android/key.properties (ver README). " +
                "Para rodar no aparelho, use `flutter build apk --release`."
        }
    }
}

flutter {
    source = "../.."
}

dependencies {
    coreLibraryDesugaring("com.android.tools:desugar_jdk_libs:2.1.4")
}
