/**
 * The backend stores timestamps as naive UTC (Python's datetime.utcnow()),
 * so the JSON it sends has no timezone marker (e.g. "2026-08-13T10:53:00").
 * Browsers interpret a timezone-less ISO string as LOCAL time, not UTC —
 * so without correction, displayed times are wrong by the viewer's UTC
 * offset. We fix that here by treating the string as UTC explicitly, then
 * formatting in IST (Asia/Kolkata) specifically, regardless of the
 * viewer's system locale.
 */
function asUtcDate(isoString) {
  if (!isoString) return null;
  // If it already has a timezone marker (Z or +hh:mm), trust it as-is.
  const hasTz = /Z$|[+-]\d{2}:?\d{2}$/.test(isoString);
  return new Date(hasTz ? isoString : `${isoString}Z`);
}

export function formatIST(isoString, { withTime = true } = {}) {
  const date = asUtcDate(isoString);
  if (!date || isNaN(date.getTime())) return "-";

  const options = {
    timeZone: "Asia/Kolkata",
    day: "2-digit",
    month: "short",
    year: "numeric",
  };
  if (withTime) {
    options.hour = "2-digit";
    options.minute = "2-digit";
    options.hour12 = true;
  }

  const formatted = date.toLocaleString("en-IN", options);
  return withTime ? `${formatted} IST` : formatted;
}
