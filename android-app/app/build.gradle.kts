import org.gradle.api.tasks.Sync

plugins {
    id("com.android.application")
    id("com.chaquo.python")
}

val repositoryRoot = rootProject.projectDir.parentFile
val webProject = repositoryRoot.resolve("app/web")
val generatedPython = layout.buildDirectory.dir("generated/bookPython")

val buildBookWeb by tasks.registering(Exec::class) {
    group = "book"
    description = "Build the React/PWA frontend for the embedded Android server."
    workingDir = webProject
    commandLine("npm.cmd", "run", "build")
    inputs.files(fileTree(webProject.resolve("src")), webProject.resolve("index.html"), webProject.resolve("vite.config.ts"))
    inputs.file(webProject.resolve("package-lock.json"))
    outputs.dir(webProject.resolve("dist"))
}

val prepareBookPython by tasks.registering(Sync::class) {
    group = "book"
    description = "Assemble Python Runtime, current canonical course assets, and built web files."
    dependsOn(buildBookWeb)
    into(generatedPython)

    from(repositoryRoot) {
        include("app/**/*.py")
        include("runtime/**/*.py")
        include("book_core/**/*.py")
        include("books/functional-analysis/**")
        include("courses/**")
        include("library/**")
        exclude("**/__pycache__/**")
        exclude("**/*.candidate")
    }
    from(webProject.resolve("dist")) {
        into("android_web")
    }
    from(project.file("src/main/python"))
}

android {
    namespace = "com.jvust.book.app"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.jvust.book.app"
        minSdk = 24
        targetSdk = 35
        versionCode = 1
        versionName = "0.1.0"

        ndk {
            abiFilters += listOf("arm64-v8a")
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = false
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}

chaquopy {
    defaultConfig {
        version = "3.11"
        buildPython("C:/Program Files/Python311/python.exe")
        pip {
            // Keep the Android resolver deterministic. These versions are the
            // same API family used by the desktop test environment.
            install("fastapi==0.115.6")
            // Pydantic v2 requires the native pydantic-core extension, which
            // is not available for Chaquopy's Android Python runtime. The
            // API adapter supports v1 and v2 validation APIs.
            install("pydantic==1.10.17")
            install("starlette==0.41.3")
            install("uvicorn==0.34.0")
            install("httpx==0.28.1")
            install("httpcore==1.0.7")
            install("anyio==4.8.0")
            install("h11==0.14.0")
            install("click==8.1.8")
            install("certifi==2024.12.14")
            install("idna==3.10")
            install("sniffio==1.3.1")
            install("typing-extensions==4.12.2")
            install("typing-inspection==0.4.1")
            install("annotated-types==0.7.0")
            install("annotated-doc==0.0.4")
        }
    }
    sourceSets {
        getByName("main") {
            setSrcDirs(listOf(generatedPython))
        }
    }
}

tasks.named("preBuild") {
    dependsOn(prepareBookPython)
}

// Chaquopy's source merge task consumes the generated source directory. Keep
// Gradle 8.13's task validation happy by declaring that dependency explicitly.
tasks.configureEach {
    if (name.startsWith("merge") && name.endsWith("PythonSources")) {
        dependsOn(prepareBookPython)
    }
}
