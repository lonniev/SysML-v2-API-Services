error id: `<none>`.
file://<WORKSPACE>/build.sbt
empty definition using pc, found symbol in pc: `<none>`.
empty definition using semanticdb
empty definition using fallback
non-local guesses:
	 -dockerSettings.
	 -dockerSettings#
	 -dockerSettings().
	 -scala/Predef.dockerSettings.
	 -scala/Predef.dockerSettings#
	 -scala/Predef.dockerSettings().
offset: 1591
uri: file://<WORKSPACE>/build.sbt
text:
```scala
name := """SysML-v2-API-Services"""
organization := "org.omg"

version := "2025-02"

javacOptions ++= Seq("-source", "11", "-target", "11", "-Xlint")

val dockerSettings: Seq[Setting[_]] = Seq(

  // add a packaging path mapper that leads to copying the resources into the image's conf directory
  Docker / mappings ++= {

    val resourcesDir: File = ( sourceDirectory.value / "main" / "resources" )
    val finder: PathFinder = resourcesDir ** "*"

    val files: Seq[File] = finder.get

    files pair rebase( resourcesDir, "/opt/docker/conf" )
  },

  // add a Docker build command to allow code within the image to write into its directories
  dockerCommands := dockerCommands.value.flatMap {
    case Cmd("USER", "1001:0") =>
      Seq(
        Cmd("RUN", "chmod -R 777 /opt/docker"),
        Cmd("USER", "1001:0"),
      )
    case cmd => Seq(cmd)
  }
)

val commonSettings: Seq[Setting[_]] = Seq(
  dockerUsername.withRank(KeyRanks.Invisible)   := Some("intercax"),
  dockerRepository.withRank(KeyRanks.Invisible) := Some("ghcr.io"),
  dockerBaseImage := "openjdk:11-jre-slim",

  // in the shell that runs SBT (or in a GHA job), the devops user
  // has to authenticate the shell with docker
  // echo $GITHUB_TOKEN | docker login ghcr.io -u lonniev --password-stdin
  Docker / version.withRank(KeyRanks.Invisible)   := s"$coreVersion-$releaseIdentifier-$buildIdentifier",
  dockerUpdateLatest.withRank(KeyRanks.Invisible) := true,
)

lazy val root = (project in file(".")).
  enablePlugins(PlayJava).
  enablePlugins(DockerPlugin).
  settings(
    commonSettings,
    dockerSetting@@s
  )

dockerExposedPorts ++= Seq(9000)

scalaVersion := "2.12.6"

libraryDependencies += guice
libraryDependencies += "org.hibernate" % "hibernate-core" % "5.4.1.Final"
libraryDependencies += "org.hibernate" % "hibernate-jpamodelgen" % "5.4.1.Final"
libraryDependencies += "org.postgresql" % "postgresql" % "42.2.5"
libraryDependencies += "com.fasterxml.jackson.core" % "jackson-annotations" % "2.9.8"
libraryDependencies += "com.fasterxml.jackson.core" % "jackson-databind" % "2.9.8"
libraryDependencies += "com.fasterxml.jackson.datatype" % "jackson-datatype-hibernate5" % "2.9.8"
libraryDependencies += "io.swagger" % "swagger-play2_2.12" % "1.6.0"
libraryDependencies += "org.reflections" % "reflections" % "0.9.10"

javacOptions ++= Seq("-s", "app")

// https://stackoverflow.com/questions/42568234/intellij-idea-support-for-immutables-with-sbt
// tell sbt (and by extension IDEA) that there is source code in target/generated_sources
managedSourceDirectories in Compile += baseDirectory.value / "generated"
// before compilation happens, create the target/generated_sources directory
compile in Compile := (compile in Compile).dependsOn(Def.task({
  (baseDirectory.value / "generated").mkdirs()
})).value
// tell the java compiler to output generated source files to target/generated_sources
javacOptions in Compile ++= Seq("-s", "generated")

sources in(Compile, doc) := Seq.empty
publishArtifact in(Compile, packageDoc) := false

// https://github.com/playframework/playframework/issues/8286#issuecomment-488733669
// hopefully fixed in Play 2.8
PlayKeys.devSettings += "play.server.http.idleTimeout" -> "infinite"

```


#### Short summary: 

empty definition using pc, found symbol in pc: `<none>`.