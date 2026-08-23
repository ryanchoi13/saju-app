import 'dart:convert';

import 'package:shared_preferences/shared_preferences.dart';

import 'models.dart';

class ProfileStore {
  static const _key = 'fortune_god_profile';

  static Future<void> save(Profile profile) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(
      _key,
      jsonEncode({
        'nickname': profile.nickname,
        'gender': profile.gender,
        'calendar_type': profile.calendarType,
        'is_leap_month': profile.isLeapMonth,
        'birth_date': profile.birthDate.toIso8601String(),
        'birth_time': profile.birthTime,
        'time_unknown': profile.timeUnknown,
        'love_status': profile.loveStatus,
        'career_status': profile.careerStatus,
      }),
    );
  }

  static Future<Profile?> load() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_key);
    if (raw == null) return null;
    return Profile.fromJson(jsonDecode(raw) as Map<String, dynamic>);
  }
}
