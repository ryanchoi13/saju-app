"""KHIDI 2023 age/sex survey-day consumption, not preferences.
Absent from the published top 100 means unknown, never zero. Malformed columns
are excluded. Small/uncertain differences produce no score. All transforms below
are editorial, not survey-authored recommendations.
"""
import json
import math
from pathlib import Path
from .menu_frequency import ANCHORS
DATA=json.loads(Path(__file__).with_name("menu_demographics_2023.json").read_text())
ALIASES={"김치볶음밥":"볶음밥/오므라이스","새우볶음밥":"볶음밥/오므라이스","계란볶음밥":"볶음밥/오므라이스", "해물볶음밥":"볶음밥/오므라이스", "햄볶음밥":"볶음밥/오므라이스", "오므라이스":"볶음밥/오므라이스", "소고기무국":"쇠고기국", "오징어뭇국":"오징어국", "북엇국":"북어국", "경양식 돈가스":"돈까스", "일본식 돈카츠":"돈까스", "치즈버거":"햄버거", "토마토파스타":"스파게티", "야채비빔밥":"비빔밥", "돌솥비빔밥":"비빔밥"}


def age_band(age):
    if age is None or age<1:return None
    for low,high,label in ((1,2,"1-2"),(3,5,"3-5"),(6,11,"6-11"),(12,18,"12-18"),(19,29,"19-29"),(30,49,"30-49"),(50,64,"50-64")):
        if low<=age<=high:return label
    return "65+"


def demographic_evidence(name,age,gender):
    label=ANCHORS[name][0] if name in ANCHORS else ALIASES.get(name,name)
    baseline=DATA["all:all"]["foods"].get(label)
    band=age_band(age)
    if not baseline or not band:
        return {"bonus":0,"status":"national_fallback","survey_food":label}
    # Age first; sex narrows only where that stratum has usable evidence.
    for sex in ([gender,"all"] if gender in {"male","female"} else ["all"]):
        group=DATA.get(sex+":"+band,{})
        record=group.get("foods",{}).get(label)
        if not record or record["rate"]<=0 or record["se"]/record["rate"]>.3:continue
        delta=record["rate"]-baseline["rate"]
        # Conservative uncertainty screen; not a formal independent-sample test.
        noise=2*math.hypot(record["se"],baseline["se"])
        bonus=0 if abs(delta)<=noise else max(-2,min(2,delta/5))
        return {"bonus":round(bonus,2),"status":"survey_age_sex" if sex!="all" else "survey_age", "survey_food":label,"age_band":band,"gender":sex,"rate":record["rate"],"se":record["se"],"national_rate":baseline["rate"],"source_url":group["source_url"],"year":2023}
    return {"bonus":0,"status":"national_fallback","survey_food":label}
