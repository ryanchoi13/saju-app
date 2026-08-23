class Profile {
  Profile({
    required this.nickname,
    required this.gender,
    required this.calendarType,
    required this.isLeapMonth,
    required this.birthDate,
    required this.timeUnknown,
    this.birthTime,
    this.loveStatus = 'solo',
    this.careerStatus = 'employee',
  });

  String nickname;
  String gender;
  String calendarType;
  bool isLeapMonth;
  DateTime birthDate;
  String? birthTime;
  bool timeUnknown;
  String loveStatus;
  String careerStatus;

  Map<String, dynamic> toJson({String? asOf, String? theme, String? period}) {
    return {
      'nickname': nickname,
      'gender': gender,
      'calendar_type': calendarType,
      'is_leap_month': isLeapMonth,
      'birth_date':
          '${birthDate.year.toString().padLeft(4, '0')}-${birthDate.month.toString().padLeft(2, '0')}-${birthDate.day.toString().padLeft(2, '0')}',
      'birth_time': timeUnknown ? null : birthTime,
      'time_unknown': timeUnknown,
      'love_status': loveStatus,
      'career_status': careerStatus,
      if (asOf != null) 'as_of': asOf,
      if (theme != null) 'theme': theme,
      if (period != null) 'period': period,
    };
  }

  factory Profile.fromJson(Map<String, dynamic> json) {
    return Profile(
      nickname: json['nickname'] as String,
      gender: json['gender'] as String,
      calendarType: json['calendarType'] as String? ?? json['calendar_type'] as String,
      isLeapMonth: json['isLeapMonth'] as bool? ?? json['is_leap_month'] as bool? ?? false,
      birthDate: DateTime.parse(json['birthDate'] as String? ?? json['birth_date'] as String),
      birthTime: json['birthTime'] as String? ?? json['birth_time'] as String?,
      timeUnknown: json['timeUnknown'] as bool? ?? json['time_unknown'] as bool? ?? true,
      loveStatus: json['loveStatus'] as String? ?? json['love_status'] as String? ?? 'solo',
      careerStatus: json['careerStatus'] as String? ?? json['career_status'] as String? ?? 'employee',
    );
  }
}

class SajuData {
  SajuData(this.raw);
  final Map<String, dynamic> raw;

  String get personality => raw['personality'] as String? ?? '';
  Map<String, dynamic> get character =>
      Map<String, dynamic>.from(raw['character'] as Map? ?? {});
  Map<String, double> get wuxing {
    final src = Map<String, dynamic>.from(raw['wuxingPercent'] as Map? ?? {});
    return src.map((k, v) => MapEntry(k, (v as num).toDouble()));
  }

  List<Map<String, dynamic>> get pillars {
    final list = raw['pillars'] as List? ?? [];
    return list.map((e) => Map<String, dynamic>.from(e as Map)).toList();
  }
}
