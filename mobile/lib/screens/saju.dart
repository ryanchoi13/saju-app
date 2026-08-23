import 'package:flutter/material.dart';

import '../models.dart';
import '../theme.dart';
import '../widgets/cards.dart';
import '../widgets/donut.dart';

class SajuScreen extends StatelessWidget {
  const SajuScreen({super.key, required this.saju, this.showClassic = false, required this.onToggleClassic});

  final SajuData? saju;
  final bool showClassic;
  final VoidCallback onToggleClassic;

  @override
  Widget build(BuildContext context) {
    if (saju == null) {
      return const Center(child: CircularProgressIndicator(color: FortuneTheme.gold));
    }
    final ch = saju!.character;
    return ListView(
      padding: const EdgeInsets.fromLTRB(20, 12, 20, 28),
      children: [
        const Text('내 사주 분석', style: TextStyle(fontSize: 22, fontWeight: FontWeight.w800)),
        const SizedBox(height: 12),
        GlassCard(
          child: Column(
            children: [
              Text('${ch['gan'] ?? ''}${ch['zhi'] ?? ''} · ${ch['animal'] ?? ''}', style: const TextStyle(color: FortuneTheme.gold)),
              const SizedBox(height: 6),
              Text(ch['title'] as String? ?? '', style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w800)),
              const SizedBox(height: 8),
              Text(ch['summary'] as String? ?? '', textAlign: TextAlign.center),
              const SizedBox(height: 8),
              Chip(label: Text('분위기 ${ch['vibe'] ?? ''}')),
            ],
          ),
        ),
        const SizedBox(height: 14),
        GlassCard(child: WuxingDonut(values: saju!.wuxing)),
        const SizedBox(height: 14),
        GlassCard(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('성격 요약', style: TextStyle(color: FortuneTheme.gold, fontWeight: FontWeight.w700)),
              const SizedBox(height: 8),
              Text(saju!.personality),
            ],
          ),
        ),
        const SizedBox(height: 14),
        SwitchListTile(
          value: showClassic,
          onChanged: (_) => onToggleClassic(),
          title: const Text('정통 만세력 표'),
          subtitle: const Text('천간·지지·십성·나음을 표로 봅니다'),
        ),
        if (showClassic)
          GlassCard(
            child: SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: DataTable(
                headingRowColor: WidgetStateProperty.all(Colors.white10),
                columns: const [
                  DataColumn(label: Text('')),
                  DataColumn(label: Text('천간')),
                  DataColumn(label: Text('지지')),
                  DataColumn(label: Text('십성')),
                  DataColumn(label: Text('나음')),
                ],
                rows: saju!.pillars
                    .map(
                      (p) => DataRow(
                        cells: [
                          DataCell(Text(p['name'] as String? ?? '')),
                          DataCell(Text('${p['ganHan'] ?? ''} ${p['gan'] ?? ''}')),
                          DataCell(Text('${p['zhiHan'] ?? ''} ${p['zhi'] ?? ''}')),
                          DataCell(Text('${p['shiShenGan'] ?? '-'}')),
                          DataCell(Text('${p['naYin'] ?? ''}')),
                        ],
                      ),
                    )
                    .toList(),
              ),
            ),
          ),
      ],
    );
  }
}
