# Enquiry v43
Removed email from the enquiry UI and new inquiry payload. Phone and WeChat are required in frontend and backend. Phone accepts common international/landline digit formats; WeChat must contain at least two nonblank characters. Existing stored inquiries and account email login remain intact.

Service selection is a semantic native radio group with rounded cards. Vehicle/city selects have a consistent custom chevron and rounded focus styling. Browser verified selection, zero email fields, required contact fields, and no overflow at 880px. Screenshots: service-choices.png and contacts.png.

42 UI templates passed, with zero English static-page Chinese leaks. Isolated backend tests passed for missing/invalid phone, missing/blank WeChat, no email requirement, consent, saving and account isolation. Preview restarted with the same private data directory.
