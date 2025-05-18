import java.time.{ZoneId, ZonedDateTime}

object Metadata {
  private val UTC = "UTC"

  // build time
  val buildTime: ZonedDateTime = ZonedDateTime.now(ZoneId.of(UTC))

  // product info
  val productName = "OMG SysMLv2 API"
  val website     = "https://omg.org"
  val copyright   = s"© ${buildTime.getYear} Object Management Group. All Rights Reserved."
}
