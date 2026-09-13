import org.gradle.api.tasks.Sync

plugins {
    id("com.android.application")
    id("com.chaquo.python")
}

val repositoryRoot = rootProject.projectDir.parentFile
val webProject = repositoryRoot.resolve("app/web")
val generatedPython = layout.buildDirectory.dir("generated/bookPython")
val generatedWeb = layout.buildDirectory.dir("generated/bookWeb")
val npmExecutable = if (System.getProperty("os.name").startsWith("Windows")) "npm.cmd" else "npm"

val buildBookWeb by tasks.registering(Exec::class) {
    group = "book"
    description = "Build the React/PWA frontend for the embedded Android server."
    workingDir = webProject
    commandLine(npmExecutable, "run", "build", "--", "--mode", "android", "--outDir", generatedWeb.get().asFile, "--emptyOutDir")
    inputs.files(fileTree(webProject.resolve("src")), fileTree(webProject.resolve("public")),
        webProject.resolve("index.html"), webProject.resolve("vite.config.ts"),
        webProject.resolve("package.json"), webProject.resolve("package-lock.json"))
    inputs.files(fileTree(webProject) { include("tsconfig*.json") })
    outputs.dir(generatedWeb)
}

val prepareBookPython by tasks.registering(Sync::class) {
    group = "book"
    description = "Assemble Python Runtime, current canonical course assets, and built web files."
    dependsOn(buildBookWeb)
    into(generatedPython)

    from(repositoryRoot) {
        include("app/__init__.py")
        include("app/api/**/*.py")
        include("app/study/**/*.py")
        include("runtime/**/*.py")
        include("book_core/**/*.py")
        include("books/functional-analysis/**")
        include("courses/**")
        include("library/**")
        exclude("**/__pycache__/**")
        exclude("**/*.candidate")
    }
    from(generatedWeb) {
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
        versionCode = 4
        versionName = "0.1.3"

        ndk {
            abiFilters += listOf("arm64-v8a", "x86_64")
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
        // CourseRuntime locates its resource root using the runtime directory.
        // Chaquopy otherwise keeps Python-only packages inside the APK archive.
        extractPackages("runtime")
        providers.gradleProperty("bookBuildPython").orElse(providers.environmentVariable("BOOK_BUILD_PYTHON"))
            .orNull?.let { buildPython(it) }
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
