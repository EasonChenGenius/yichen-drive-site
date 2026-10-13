# Structured enquiry v44
Removed the free-text itinerary field. Pickup, return, destination, duration, half-hour times and bag sizes use curated options. People and bag counts also use selects. City changes update pickup and return lists. Airport transfer direction restricts the airport side to the two listed Chengdu airports; flight status is selected, actual flight number remains for staff confirmation until a live flight source is connected.

Frontend phone pattern is [0-9]{11}, maxlength/minlength 11. Backend requires the same 11 ASCII digits. Tests reject 10 and 12 digits, spaced and full-width digits, arbitrary locations, invalid times and bag sizes. Positive structured enquiries save canonical place names derived on the server. Backend checks city membership, airport side, allowed duration and same-day time order. Legacy inquiries remain readable.

Isolated API validation and account isolation passed. 42 English template/state checks passed. Browser confirmed no itinerary textarea, airport options and ten-digit rejection. Screenshot itinerary.png. Existing user-filled tab was preserved; a fresh preview tab was used for checks.
