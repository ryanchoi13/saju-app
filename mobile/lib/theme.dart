import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class FortuneTheme {
  static const navy = Color(0xFF12162A);
  static const navy2 = Color(0xFF1B2140);
  static const gold = Color(0xFFE8C87A);
  static const cream = Color(0xFFF6EFE0);
  static const coral = Color(0xFFE07A5F);
  static const mint = Color(0xFF7DCFB6);

  static ThemeData dark() {
    final base = ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      scaffoldBackgroundColor: navy,
      colorScheme: const ColorScheme.dark(
        primary: gold,
        secondary: mint,
        surface: navy2,
        error: coral,
      ),
    );
    return base.copyWith(
      textTheme: GoogleFonts.notoSansKrTextTheme(base.textTheme).apply(
        bodyColor: cream,
        displayColor: cream,
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: Colors.transparent,
        elevation: 0,
        centerTitle: true,
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: navy2,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(16),
          borderSide: BorderSide.none,
        ),
      ),
    );
  }
}

const wuxingColors = {
  '목': Color(0xFF6BCB77),
  '화': Color(0xFFE07A5F),
  '토': Color(0xFFE8C87A),
  '금': Color(0xFFE8E6E3),
  '수': Color(0xFF6B9AC4),
};
