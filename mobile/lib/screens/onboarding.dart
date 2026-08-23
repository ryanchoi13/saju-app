import 'package:flutter/material.dart';

import '../api.dart';
import '../models.dart';
import '../profile_store.dart';
import '../theme.dart';
import '../widgets/cards.dart';

const loveOptions = {
  'solo': '솔로',
  'dating': '썸·연애 중',
  'married': '기혼',
  'reunion': '이별·재회 고민',
};

const careerOptions = {
  'employee': '직장인',
  'student': '학생·취준생',
  'freelance': '사업·프리랜서',
  'job_change': '이직·퇴사 준비',
};

class OnboardingScreen extends StatefulWidget {
  const OnboardingScreen({super.key, required this.api, this.existing, required this.onDone});

  final FortuneApi api;
  final Profile? existing;
  final void Function(Profile profile) onDone;

  @override
  State<OnboardingScreen> createState() => _OnboardingScreenState();
}

class _OnboardingScreenState extends State<OnboardingScreen> {
  late final TextEditingController _nick;
  String gender = 'female';
  String calendarType = 'solar';
  bool leap = false;
  bool timeUnknown = false;
  DateTime birth = DateTime(1995, 5, 15);
  TimeOfDay clock = const TimeOfDay(hour: 12, minute: 0);
  String love = 'solo';
  String career = 'employee';
  bool loading = false;
  String? error;

  @override
  void initState() {
    super.initState();
    final p = widget.existing;
    _nick = TextEditingController(text: p?.nickname ?? '');
    if (p != null) {
      gender = p.gender;
      calendarType = p.calendarType;
      leap = p.isLeapMonth;
      timeUnknown = p.timeUnknown;
      birth = p.birthDate;
      love = p.loveStatus;
      career = p.careerStatus;
      if (p.birthTime != null) {
        final parts = p.birthTime!.split(':');
        clock = TimeOfDay(hour: int.parse(parts[0]), minute: int.parse(parts[1]));
      }
    }
  }

  @override
  void dispose() {
    _nick.dispose();
    super.dispose();
  }

  Future<void> _pickDate() async {
    final next = await showDatePicker(
      context: context,
      initialDate: birth,
      firstDate: DateTime(1930),
      lastDate: DateTime.now(),
    );
    if (next != null) setState(() => birth = next);
  }

  Future<void> _pickTime() async {
    final next = await showTimePicker(context: context, initialTime: clock);
    if (next != null) setState(() => clock = next);
  }

  Future<void> _submit() async {
    if (_nick.text.trim().isEmpty) {
      setState(() => error = '닉네임을 입력해 주세요.');
      return;
    }
    final profile = Profile(
      nickname: _nick.text.trim(),
      gender: gender,
      calendarType: calendarType,
      isLeapMonth: calendarType == 'lunar' && leap,
      birthDate: birth,
      timeUnknown: timeUnknown,
      birthTime: timeUnknown
          ? null
          : '${clock.hour.toString().padLeft(2, '0')}:${clock.minute.toString().padLeft(2, '0')}:00',
      loveStatus: love,
      careerStatus: career,
    );
    setState(() {
      loading = true;
      error = null;
    });
    try {
      await widget.api.saveProfile(profile);
      await ProfileStore.save(profile);
      widget.onDone(profile);
    } catch (e) {
      setState(() => error = '연결에 실패했습니다. 백엔드가 켜져 있는지 확인해 주세요.\n$e');
    } finally {
      if (mounted) setState(() => loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(20, 24, 20, 40),
          children: [
            const Text('운세의신', style: TextStyle(fontSize: 28, fontWeight: FontWeight.w800, color: FortuneTheme.gold)),
            const SizedBox(height: 6),
            const Text('캐주얼하게, 만세력은 정확하게.', style: TextStyle(color: Colors.white70)),
            const SizedBox(height: 24),
            GlassCard(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  TextField(
                    controller: _nick,
                    decoration: const InputDecoration(labelText: '닉네임'),
                  ),
                  const SizedBox(height: 16),
                  const Text('성별'),
                  const SizedBox(height: 8),
                  ChoiceChipRow(
                    options: const {'male': '남', 'female': '여'},
                    value: gender,
                    onChanged: (v) => setState(() => gender = v),
                  ),
                  const SizedBox(height: 16),
                  const Text('생년월일'),
                  const SizedBox(height: 8),
                  ChoiceChipRow(
                    options: const {'solar': '양력', 'lunar': '음력'},
                    value: calendarType,
                    onChanged: (v) => setState(() => calendarType = v),
                  ),
                  if (calendarType == 'lunar') ...[
                    const SizedBox(height: 8),
                    SwitchListTile(
                      contentPadding: EdgeInsets.zero,
                      title: const Text('윤달'),
                      value: leap,
                      onChanged: (v) => setState(() => leap = v),
                    ),
                  ],
                  ListTile(
                    contentPadding: EdgeInsets.zero,
                    title: Text('${birth.year}년 ${birth.month}월 ${birth.day}일'),
                    trailing: const Icon(Icons.calendar_month, color: FortuneTheme.gold),
                    onTap: _pickDate,
                  ),
                  SwitchListTile(
                    contentPadding: EdgeInsets.zero,
                    title: const Text('태어난 시간 모름'),
                    subtitle: const Text('선택 시 삼주(6글자)만 계산합니다'),
                    value: timeUnknown,
                    onChanged: (v) => setState(() => timeUnknown = v),
                  ),
                  if (!timeUnknown)
                    ListTile(
                      contentPadding: EdgeInsets.zero,
                      title: Text('${clock.hour.toString().padLeft(2, '0')}:${clock.minute.toString().padLeft(2, '0')}'),
                      trailing: const Icon(Icons.schedule, color: FortuneTheme.gold),
                      onTap: _pickTime,
                    ),
                ],
              ),
            ),
            const SizedBox(height: 16),
            GlassCard(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('애정 상태'),
                  const SizedBox(height: 8),
                  ChoiceChipRow(options: loveOptions, value: love, onChanged: (v) => setState(() => love = v)),
                  const SizedBox(height: 16),
                  const Text('직업·상황'),
                  const SizedBox(height: 8),
                  ChoiceChipRow(options: careerOptions, value: career, onChanged: (v) => setState(() => career = v)),
                ],
              ),
            ),
            if (error != null) ...[
              const SizedBox(height: 12),
              Text(error!, style: const TextStyle(color: FortuneTheme.coral)),
            ],
            const SizedBox(height: 20),
            FilledButton(
              onPressed: loading ? null : _submit,
              style: FilledButton.styleFrom(
                backgroundColor: FortuneTheme.gold,
                foregroundColor: FortuneTheme.navy,
                padding: const EdgeInsets.symmetric(vertical: 16),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
              ),
              child: Text(loading ? '사주 계산 중...' : '운세 보기'),
            ),
          ],
        ),
      ),
    );
  }
}
