import 'package:flutter/material.dart';

import '../api.dart';
import '../models.dart';
import '../theme.dart';
import '../widgets/cards.dart';

class HomeScreen extends StatelessWidget {
  const HomeScreen({
    super.key,
    required this.profile,
    required this.today,
    required this.onRefresh,
    required this.onEdit,
  });

  final Profile profile;
  final Map<String, dynamic>? today;
  final VoidCallback onRefresh;
  final VoidCallback onEdit;

  @override
  Widget build(BuildContext context) {
    final score = today?['score'] as int? ?? 0;
    return ListView(
      padding: const EdgeInsets.fromLTRB(20, 12, 20, 28),
      children: [
        Row(
          children: [
            Expanded(
              child: Text(
                '${profile.nickname}님의 오늘',
                style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w800),
              ),
            ),
            IconButton(onPressed: onEdit, icon: const Icon(Icons.edit_outlined, color: FortuneTheme.gold)),
            IconButton(onPressed: onRefresh, icon: const Icon(Icons.refresh, color: FortuneTheme.gold)),
          ],
        ),
        const SizedBox(height: 8),
        GlassCard(
          child: Row(
            children: [
              ScoreRing(score: score),
              const SizedBox(width: 18),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(today?['title'] as String? ?? '오늘의 운세', style: const TextStyle(color: FortuneTheme.gold)),
                    const SizedBox(height: 8),
                    Text(today?['summary'] as String? ?? '사주를 불러오는 중입니다.'),
                    const SizedBox(height: 12),
                    Wrap(
                      spacing: 8,
                      children: [
                        Chip(label: Text('색 ${today?['luckyColor'] ?? '-'}')),
                        Chip(label: Text('숫자 ${(today?['luckyNumbers'] as List? ?? []).join(', ')}')),
                      ],
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 14),
        GlassCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('오늘의 조언', style: TextStyle(color: FortuneTheme.gold, fontWeight: FontWeight.w700)),
              const SizedBox(height: 8),
              Text(today?['advice'] as String? ?? ''),
            ],
          ),
        ),
      ],
    );
  }
}
