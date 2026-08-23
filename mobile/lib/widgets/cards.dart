import 'package:flutter/material.dart';

import '../theme.dart';

class GlassCard extends StatelessWidget {
  const GlassCard({super.key, required this.child, this.padding = const EdgeInsets.all(18)});

  final Widget child;
  final EdgeInsets padding;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: padding,
      decoration: BoxDecoration(
        color: FortuneTheme.navy2,
        borderRadius: BorderRadius.circular(22),
        border: Border.all(color: FortuneTheme.gold.withValues(alpha: 0.18)),
      ),
      child: child,
    );
  }
}

class ScoreRing extends StatelessWidget {
  const ScoreRing({super.key, required this.score});
  final int score;

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        SizedBox(
          width: 92,
          height: 92,
          child: Stack(
            alignment: Alignment.center,
            children: [
              CircularProgressIndicator(
                value: score / 100,
                strokeWidth: 8,
                color: FortuneTheme.gold,
                backgroundColor: Colors.white12,
              ),
              Text(
                '$score',
                style: const TextStyle(fontSize: 26, fontWeight: FontWeight.w800, color: FortuneTheme.gold),
              ),
            ],
          ),
        ),
        const SizedBox(height: 8),
        const Text('행운 점수', style: TextStyle(color: Colors.white70, fontSize: 12)),
      ],
    );
  }
}

class ChoiceChipRow extends StatelessWidget {
  const ChoiceChipRow({
    super.key,
    required this.options,
    required this.value,
    required this.onChanged,
  });

  final Map<String, String> options;
  final String value;
  final ValueChanged<String> onChanged;

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: options.entries.map((e) {
        final selected = e.key == value;
        return ChoiceChip(
          label: Text(e.value),
          selected: selected,
          onSelected: (_) => onChanged(e.key),
          selectedColor: FortuneTheme.gold,
          labelStyle: TextStyle(color: selected ? FortuneTheme.navy : FortuneTheme.cream),
        );
      }).toList(),
    );
  }
}
