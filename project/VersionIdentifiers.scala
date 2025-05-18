import java.time.format.DateTimeFormatter
import java.time.ZoneId
import Metadata.buildTime

// Reference: https://semver.org/
object VersionIdentifiers {
  private val timeZoneForBuildIdentifier       = "US/Eastern"
  private val dateTimeFormatForBuildIdentifier = "yyyy-MM-dd_HHmmss"

  private val majorVersion = "2"
  private val minorVersion = "0"

  val coreVersion = s"$majorVersion.$minorVersion"

  // SNAPSHOT/INTERNAL - for internal releases
  // M1, M2 .. M(n) - for milestone releases
  // SP1, SP2 .. SP(n) - for service pack releases
  val releaseIdentifier: String = "Internal"

  // current date time as per a particular time zone
  val buildIdentifier: String =
    buildTime
      .withZoneSameInstant(ZoneId.of(timeZoneForBuildIdentifier))
      .format(DateTimeFormatter.ofPattern(dateTimeFormatForBuildIdentifier))
}
