# Date range v45 verification

- Start and end dates are explicitly shown alongside their time selects. Start date and duration update the end date; manual end-date changes update the calendar-day count (inclusive of both dates).
- Browser verified Nov 20 plus 3 days -> Nov 22, and manually changing end date to Nov 23 -> 4 days.
- API tests with isolated database passed multi-day save, malformed dates, reversed dates, equal/reversed same-day times, date-duration mismatch, contact validation and account isolation. Server derives startAt/endAt and checks end > start. No real customer database used for tests.
- Airport direction and flight status removed from form and newly saved inquiries; existing historical records preserved. Curated location and 11-digit phone checks remain active.
- 42 UI template/state checks passed with zero English text leaks. Screenshot: date-range.png.
- Live preview runs on port 8766 using the existing private data directory. No payment or notification integration added.
