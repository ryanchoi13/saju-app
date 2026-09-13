# Fashion v2 weather layer — stage 1

DALHA's Korea-only first rollout uses one fixed forecast point in Gyeongju. It does not request browser GPS permission, receive user coordinates, or store location data. Korean language, Celsius, km/h, and Asia/Seoul time are fixed. Location and language expansion are deferred.

Calendar season continues to influence colour mood. Clothing thickness is classified separately from hourly apparent temperature. The classifier uses the daytime high (11:00–17:00), evening low (18:00–23:00), morning/evening spread, precipitation probability and amount, sustained wind and gusts, and daytime humidity.

The eight thermal bands are: very hot (29°C+), hot (25–28.9°C), warm (22–24.9°C), mild (19–21.9°C), cool (16–18.9°C), chilly (11–15.9°C), cold (5–10.9°C), and freezing (below 5°C). A hot or warm day with an evening below 22°C or a 5°C+ spread adds a carry-only windbreaker or long-sleeve shirt rather than dressing the user in a heavy autumn layer all day.

Rain at 40%+ probability or 1 mm+ total precipitation excludes suede and prefers water-resistant materials. Sustained wind at 20 km/h+ or gusts at 35 km/h+ prefers a wind-blocking shell. Hot weather with daytime humidity at 70%+ prefers breathable materials.

Stage 1 is a pure decision layer with an Open-Meteo adapter. Stage 2 will map the thermal profile into gender/TPO Daily and Trend templates before any replacement fashion-board images are produced.
