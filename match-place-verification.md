# Match place selection verification

Version: 20261010-match-places-v22.

## Implemented

Starting point and destination are searchable ARIA comboboxes using saved real service cities, public landmarks and destination records. A visible label alone is not enough: a selected known place ID is required. Editing the label clears that ID and removes the stale recommendation. Unknown text, missing choices and identical endpoints are rejected with a field error. Arrow keys, Enter, Escape, Tab and pointer selection are supported.

Recommendation body-type comparisons now use both endpoints, mountain/nearby/city/intercity categories, travellers and luggage needs. Verified insufficient seat/luggage capacity is excluded. Vehicles awaiting quotes are excluded from demo-price budget ranking. Unknown actual capacity, equipment, range and mountain suitability remain unconfirmed. No live distance, time, traffic, availability or all-in quote is fabricated. A route panel links to existing itinerary/destination information; the Four Sisters/Shuangqiao visitor note links to https://www.sgns.cn/understand/sqg (checked in the preceding turn).

## Evidence

Actual browser interactions from 2026-10-09: `design/match-place-qa/invalid-destination.png`, `destination-options.png`, `picker-final.png`, `route-recommendation.png`. The invalid word 洗澡 yielded a destination field error and zero recommendation results. A 四姑娘 search yielded the known 四姑娘山 option; ArrowDown/Enter selected it. The 700 budget had no matching mountain-category candidates; increasing the budget to 1500 displayed the X5 category candidate with the actual selected route. A later 青城 search and submission worked; browser warning/error logs were empty. A 728 px narrow layout was captured without horizontal overflow. The earlier X5 screenshot contains wording that was subsequently tightened to avoid inferring fuel equipment from body category; use the current module/copy.

2026-10-10: the final copy adjustment briefly introduced an out-of-scope variable in ranking; the regression gate caught it, it was corrected, and all 41 page templates and functional checks then passed. Checks cover arbitrary text, known text without selected IDs, identical endpoints, outbound/inbound mountain routes, intercity airport/city routes, budget gaps, group categories, confirmed insufficient capacity and English reasons.

The local server had stopped and was restarted at 127.0.0.1:8766 with the existing `work/yichen-service-data/accounts.sqlite3`. The current in-app browser went to its generated data: connection error page before restart, and then refused automated navigation from that error page. No alternative browser or bypass was used. Fresh English browser interaction remains unverified; bilingual template checks passed. The user can open the supplied normal HTTP preview address.

## Separate unfinished scope

Destination photo expansion still awaits the Manus report described in `destination-expansion-status.md`. This verification does not mark the photo catalogue, exact vehicle/interior models or the whole site's phone QA complete.


## Preference correction — 2026-10-10

The original ranking did not use the selected priority, so the user's 700-budget city trip with luxury preference displayed the cheapest Jetta. Luxury now restricts candidates to luxury/executive model positioning; H7 classification is sourced at model-family level in `visual-assets/model-positioning.json`, with no seat/material/equipment inference. The user's exact start, destination, travellers, luggage, weekend category and 700 budget were restored through visible UI controls. The real browser returned H7 at demo 680 with a dedicated luxury reason, a loaded photo and zero warning/error logs. Proof: `luxury-preference-fixed.jpg`, `luxury-reason-fixed.jpg`.

Automated checks also verify luxury E-Class candidates at 1000, mountain-route budget gaps without silently raising the budget, price-first Jetta ordering, MPV/SUV space categories, electric category and sports-car category. Unverified comfort is explicitly disclosed in its own reason. The priority is category comparison, not a guarantee of actual cabin equipment or live availability.
