import 'dart:math' as math;

import 'package:flutter/material.dart';

import '../theme.dart';

class WuxingDonut extends StatelessWidget {
  const WuxingDonut({super.key, required this.values});

  final Map<String, double> values;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: 220,
      child: Row(
        children: [
          Expanded(
            child: CustomPaint(
              painter: _DonutPainter(values),
              child: const SizedBox.expand(),
            ),
          ),
          const SizedBox(width: 12),
          Column(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: values.entries
                .map(
                  (e) => Padding(
                    padding: const EdgeInsets.symmetric(vertical: 4),
                    child: Row(
                      children: [
                        Container(
                          width: 10,
                          height: 10,
                          decoration: BoxDecoration(
                            color: wuxingColors[e.key],
                            shape: BoxShape.circle,
                          ),
                        ),
                        const SizedBox(width: 8),
                        Text('${e.key}  ${e.value.toStringAsFixed(1)}%'),
                      ],
                    ),
                  ),
                )
                .toList(),
          ),
        ],
      ),
    );
  }
}

class _DonutPainter extends CustomPainter {
  _DonutPainter(this.values);
  final Map<String, double> values;

  @override
  void paint(Canvas canvas, Size size) {
    final center = size.center(Offset.zero);
    final radius = math.min(size.width, size.height) / 2 - 8;
    final rect = Rect.fromCircle(center: center, radius: radius);
    var start = -math.pi / 2;
    final total = values.values.fold<double>(0, (a, b) => a + b);
    for (final entry in values.entries) {
      final sweep = (entry.value / (total == 0 ? 1 : total)) * math.pi * 2;
      final paint = Paint()
        ..style = PaintingStyle.stroke
        ..strokeWidth = 28
        ..strokeCap = StrokeCap.butt
        ..color = wuxingColors[entry.key] ?? Colors.white;
      canvas.drawArc(rect, start, sweep, false, paint);
      start += sweep;
    }
    final inner = Paint()..color = FortuneTheme.navy2;
    canvas.drawCircle(center, radius - 22, inner);
    final text = TextPainter(
      text: const TextSpan(
        text: '오행',
        style: TextStyle(color: FortuneTheme.gold, fontSize: 16, fontWeight: FontWeight.w700),
      ),
      textDirection: TextDirection.ltr,
    )..layout();
    text.paint(canvas, center - Offset(text.width / 2, text.height / 2));
  }

  @override
  bool shouldRepaint(covariant _DonutPainter oldDelegate) => oldDelegate.values != values;
}
