import 'package:flutter/material.dart';

import '../api.dart';
import '../models.dart';
import '../theme.dart';
import '../widgets/cards.dart';
import 'onboarding.dart';

const themes = [
  ('health', '건강', Icons.favorite_outline),
  ('wealth', '재물', Icons.savings_outlined),
  ('love', '애정', Icons.favorite),
  ('business', '사업', Icons.storefront_outlined),
  ('study', '학업', Icons.menu_book_outlined),
  ('career', '직장', Icons.work_outline),
];

class ThemesScreen extends StatelessWidget {
  const ThemesScreen({super.key, required this.api, required this.profile, required this.onProfile});

  final FortuneApi api;
  final Profile profile;
  final ValueChanged<Profile> onProfile;

  @override
  Widget build(BuildContext context) {
    return ListView(
      padding: const EdgeInsets.fromLTRB(20, 12, 20, 28),
      children: [
        const Text('테마별 운세', style: TextStyle(fontSize: 22, fontWeight: FontWeight.w800)),
        const SizedBox(height: 8),
        Text(
          '애정: ${loveOptions[profile.loveStatus]} · 상황: ${careerOptions[profile.careerStatus]}',
          style: const TextStyle(color: Colors.white70),
        ),
        const SizedBox(height: 16),
        ...themes.map(
          (t) => Padding(
            padding: const EdgeInsets.only(bottom: 10),
            child: ListTile(
              tileColor: FortuneTheme.navy2,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
              leading: Icon(t.$3, color: FortuneTheme.gold),
              title: Text(t.$2),
              trailing: const Icon(Icons.chevron_right),
              onTap: () => Navigator.of(context).push(
                MaterialPageRoute(
                  builder: (_) => ThemeDetailScreen(api: api, profile: profile, theme: t.$1, title: t.$2),
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }
}

class ThemeDetailScreen extends StatefulWidget {
  const ThemeDetailScreen({
    super.key,
    required this.api,
    required this.profile,
    required this.theme,
    required this.title,
  });

  final FortuneApi api;
  final Profile profile;
  final String theme;
  final String title;

  @override
  State<ThemeDetailScreen> createState() => _ThemeDetailScreenState();
}

class _ThemeDetailScreenState extends State<ThemeDetailScreen> {
  Map<String, dynamic>? data;
  String? error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final res = await widget.api.theme(widget.profile, widget.theme);
      setState(() => data = res);
    } catch (e) {
      setState(() => error = '$e');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(widget.title)),
      body: data == null
          ? Center(child: error == null ? const CircularProgressIndicator(color: FortuneTheme.gold) : Text('$error'))
          : ListView(
              padding: const EdgeInsets.all(20),
              children: [
                GlassCard(
                  child: Row(
                    children: [
                      ScoreRing(score: data!['score'] as int? ?? 0),
                      const SizedBox(width: 16),
                      Expanded(child: Text(data!['summary'] as String? ?? '')),
                    ],
                  ),
                ),
                const SizedBox(height: 12),
                GlassCard(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text('맞춤 조언', style: TextStyle(color: FortuneTheme.gold, fontWeight: FontWeight.w700)),
                      const SizedBox(height: 8),
                      Text(data!['advice'] as String? ?? ''),
                    ],
                  ),
                ),
              ],
            ),
    );
  }
}

class PeriodScreen extends StatefulWidget {
  const PeriodScreen({super.key, required this.api, required this.profile});

  final FortuneApi api;
  final Profile profile;

  @override
  State<PeriodScreen> createState() => _PeriodScreenState();
}

class _PeriodScreenState extends State<PeriodScreen> with SingleTickerProviderStateMixin {
  late final TabController _tabs;
  Map<String, dynamic>? month;
  Map<String, dynamic>? year;
  String? error;

  @override
  void initState() {
    super.initState();
    _tabs = TabController(length: 2, vsync: this);
    _load();
  }

  @override
  void dispose() {
    _tabs.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    try {
      final m = await widget.api.period(widget.profile, 'month');
      final y = await widget.api.period(widget.profile, 'year');
      setState(() {
        month = m;
        year = y;
      });
    } catch (e) {
      setState(() => error = '$e');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        TabBar(
          controller: _tabs,
          indicatorColor: FortuneTheme.gold,
          labelColor: FortuneTheme.gold,
          tabs: const [Tab(text: '이달의 운세'), Tab(text: '올해의 운세')],
        ),
        Expanded(
          child: error != null
              ? Center(child: Text(error!))
              : TabBarView(
                  controller: _tabs,
                  children: [
                    _PeriodBody(data: month),
                    _PeriodBody(data: year),
                  ],
                ),
        ),
      ],
    );
  }
}

class _PeriodBody extends StatelessWidget {
  const _PeriodBody({required this.data});
  final Map<String, dynamic>? data;

  @override
  Widget build(BuildContext context) {
    if (data == null) {
      return const Center(child: CircularProgressIndicator(color: FortuneTheme.gold));
    }
    final themes = (data!['themes'] as List? ?? []).map((e) => Map<String, dynamic>.from(e as Map)).toList();
    return ListView(
      padding: const EdgeInsets.all(20),
      children: [
        GlassCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(data!['title'] as String? ?? '', style: const TextStyle(color: FortuneTheme.gold)),
              const SizedBox(height: 8),
              Text(data!['headline'] as String? ?? '', style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
              const SizedBox(height: 8),
              Text(data!['advice'] as String? ?? ''),
            ],
          ),
        ),
        const SizedBox(height: 12),
        ...themes.map(
          (t) => Padding(
            padding: const EdgeInsets.only(bottom: 10),
            child: GlassCard(
              child: Row(
                children: [
                  ScoreRing(score: t['score'] as int? ?? 0),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(t['title'] as String? ?? '', style: const TextStyle(fontWeight: FontWeight.w700)),
                        const SizedBox(height: 6),
                        Text(t['summary'] as String? ?? ''),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ],
    );
  }
}
