import java.time.ZoneId
import Metadata._
import VersionIdentifiers._
import com.typesafe.sbt.packager.docker.Cmd
import sbt.io.Path.rebase
import com.amazonaws.regions.{Region, Regions}

import scala.sys.process._

name := """SysML-v2-API-Services"""
organization := "org.omg"

version := "2025-02"

javacOptions ++= Seq("-source", "11", "-target", "11", "-Xlint")

enablePlugins(EcrPlugin)
( Docker / packageName ) := "sysml-at-your-service-image"

( Docker / version ) := version.value

Ecr / region           := Region.getRegion(Regions.US_EAST_1)
Ecr / repositoryName   := (Docker / packageName).value

Ecr / repositoryTags := Seq((Docker / version).value, "latest" )


// Create the repository before authentication takes place (optional)
Ecr / login := ((Ecr / login) dependsOn (Ecr / createRepository)).value

// Authenticate and publish a local Docker image before pushing to ECR
Ecr / push := ((Ecr / push) dependsOn (Docker / publishLocal, Ecr / login)).value

// after the routine ECR push, we also need to docker tag the image for AWS Marketplace and push that
// docker tag sysml-at-your-service-image:2025-02 709825985650.dkr.ecr.us-east-1.amazonaws.com/sysml-at-your-service/sysml-at-your-service-image:2025-02
// docker push 709825985650.dkr.ecr.us-east-1.amazonaws.com/sysml-at-your-service/sysml-at-your-service-image:2025-02

// Add this to your build.sbt file

// Define a new configuration for marketplace tasks
lazy val market = taskKey[Unit]("AWS Marketplace operations")

// Define the push task in the market namespace
lazy val marketPush = taskKey[Unit]("Push to AWS Marketplace ECR")

// AWS Marketplace ECR repository details
val marketplaceAccountId = "709825985650"
val marketplaceRepoPath = "sysml-at-your-service"
val marketplaceRegion = "us-east-1"

// Implementation of the market:push task
marketPush := {
  val log = streams.value.log
  val sourceImage = (Docker / packageName).value + ":" + (Docker / version).value
  val targetImage = s"$marketplaceAccountId.dkr.ecr.$marketplaceRegion.amazonaws.com/$marketplaceRepoPath/${(Docker / packageName).value}:${(Docker / version).value}"
  
  // First ensure the image is pushed to our ECR
  (Ecr / push).value
  
  log.info(s"Tagging $sourceImage as $targetImage")
  val tagCmd = Seq("docker", "tag", sourceImage, targetImage)
  val tagResult = Process(tagCmd).!
  
  if (tagResult != 0) {
    throw new RuntimeException(s"Failed to tag image: $sourceImage as $targetImage")
  }
  
  log.info(s"Pushing $targetImage to AWS Marketplace ECR")
  val pushCmd = Seq("docker", "push", targetImage)
  val pushResult = Process(pushCmd).!
  
  if (pushResult != 0) {
    throw new RuntimeException(s"Failed to push image to AWS Marketplace ECR: $targetImage")
  }
  
  log.info(s"Successfully pushed $targetImage to AWS Marketplace ECR")
}

// Add the task to the market namespace
market / push := marketPush.value

dockerExposedPorts ++= Seq(9000)

val dockerSettings: Seq[Setting[_]] = Seq(

  dockerBaseImage := "openjdk:11-jdk-slim",

  // in the shell that runs SBT (or in a GHA job), the devops user
  // has to authenticate the shell with docker
  // echo $GITHUB_TOKEN | docker login ghcr.io -u lonniev --password-stdin
  Docker / version.withRank(KeyRanks.Invisible)   := "2025-02",
  dockerUpdateLatest.withRank(KeyRanks.Invisible) := true,

  // add a packaging path mapper that leads to copying the resources into the image's conf directory
  Docker / mappings ++= {

    val resourcesDir: File = ( sourceDirectory.value / "main" / "resources" )
    val finder: PathFinder = resourcesDir ** "*"

    val files: Seq[File] = finder.get

    files pair rebase( resourcesDir, "/opt/docker/conf" )
  },

  // add a Docker build command to allow code within the image to write into its directories
  dockerCommands := dockerCommands.value.flatMap {
    case Cmd("EXPOSE", "9000") =>
      Seq(
        Cmd("RUN", "chmod", "-R", "777", "/opt/docker"),
        Cmd("RUN", "chown", "-R", "1001:1001", "/opt/docker"),
        Cmd("EXPOSE", "9000"),
      )
    case cmd => Seq(cmd)
  }
)

dockerEnvVars := Map(
  "DB_HOST" -> "mydbhost",
  "DB_PORT" -> "5432",
  "DB_NAME" -> "sysml2",
  "DB_USER" -> "postgres",
  "DB_PASSWORD" -> "mysecretpassword",
  "JAVA_OPTS" -> "-Ddb.host=mydbhost -Ddb.port=5432 -Ddb.name=sysml2 -Ddb.user=postgres -Ddb.password=mysecretpassword"
  )

lazy val root = (project in file(".")).
  enablePlugins(PlayJava).
  enablePlugins(DockerPlugin).
  settings(
    dockerSettings
  )

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
