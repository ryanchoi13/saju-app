import 'package:flutter/material.dart';

import 'api.dart';
import 'models.dart';
import 'profile_store.dart';
import 'screens/home.dart';
import 'screens/onboarding.dart';
import 'screens/saju.dart';
import 'screens/themes.dart';
import 'theme.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const FortuneGodApp());
}

class FortuneGodApp extends StatelessWidget {
  const FortuneGodApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: '운세의신',
      debugShowCheckedModeBanner: false,
      theme: FortuneTheme.dark(),
      home: const BootScreen(),
    );
  }
}

class BootScreen extends StatefulWidget {
  const BootScreen({super.key});

  @override
  State<BootScreen> createState() => _BootScreenState();
}

class _BootScreenState extends State<BootScreen> {
  final api = FortuneApi();
  Profile? profile;

  @override
  void initState() {
    super.initState();
    ProfileStore.load().then((value) {
      if (mounted) setState(() => profile = value);
    });
  }

  @override
  Widget build(BuildContext context) {
    if (profile == null) {
      return OnboardingScreen(
        api: api,
        onDone: (p) => setState(() => profile = p),
      );
    }
    return AppShell(
      api: api,
      profile: profile!,
      onProfile: (p) => setState(() => profile = p),
    );
  }
}

class AppShell extends StatefulWidget {
  const AppShell({super.key, required this.api, required this.profile, required this.onProfile});

  final FortuneApi api;
  final Profile profile;
  final ValueChanged<Profile> onProfile;

  @override
  State<AppShell> createState() => _AppShellState();
}

class _AppShellState extends State<AppShell> {
  int index = 0;
  Map<String, dynamic>? analyze;
  bool classic = false;
  String? error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void didUpdateWidget(covariant AppShell oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.profile.nickname != widget.profile.nickname ||
        oldWidget.profile.birthDate != widget.profile.birthDate ||
        oldWidget.profile.loveStatus != widget.profile.loveStatus ||
        oldWidget.profile.careerStatus != widget.profile.careerStatus) {
      _load();
    }
  }

  Future<void> _load() async {
    try {
      final res = await widget.api.analyze(widget.profile);
      setState(() {
        analyze = res;
        error = null;
      });
    } catch (e) {
      setState(() => error = '$e');
    }
  }

  void _edit() {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => OnboardingScreen(
          api: widget.api,
          existing: widget.profile,
          onDone: (p) {
            Navigator.of(context).pop();
            widget.onProfile(p);
          },
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final saju = analyze == null ? null : SajuData(Map<String, dynamic>.from(analyze!['saju'] as Map));
    final today = analyze == null ? null : Map<String, dynamic>.from(analyze!['today'] as Map);
    final pages = [
      HomeScreen(profile: widget.profile, today: today, onRefresh: _load, onEdit: _edit),
      SajuScreen(saju: saju, showClassic: classic, onToggleClassic: () => setState(() => classic = !classic)),
      ThemesScreen(api: widget.api, profile: widget.profile, onProfile: widget.onProfile),
      PeriodScreen(api: widget.api, profile: widget.profile),
    ];

    return Scaffold(
      appBar: AppBar(
        title: const Text('운세의신'),
      ),
      body: error != null
          ? Center(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(error!, textAlign: TextAlign.center),
                    const SizedBox(height: 12),
                    FilledButton(onPressed: _load, child: const Text('다시 시도')),
                  ],
                ),
              ),
            )
          : pages[index],
      bottomNavigationBar: NavigationBar(
        selectedIndex: index,
        onDestinationSelected: (i) => setState(() => index = i),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.wb_sunny_outlined), label: '오늘'),
          NavigationDestination(icon: Icon(Icons.auto_awesome), label: '사주'),
          NavigationDestination(icon: Icon(Icons.grid_view_rounded), label: '테마'),
          NavigationDestination(icon: Icon(Icons.calendar_month_outlined), label: '기간'),
        ],
      ),
    );
  }
}
