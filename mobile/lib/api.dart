import 'dart:convert';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;

import 'models.dart';

String defaultBaseUrl() {
  if (kIsWeb) return 'http://127.0.0.1:8000';
  if (Platform.isAndroid) return 'http://10.0.2.2:8000';
  return 'http://127.0.0.1:8000';
}

class FortuneApi {
  FortuneApi({String? baseUrl}) : baseUrl = baseUrl ?? defaultBaseUrl();

  final String baseUrl;

  Future<Map<String, dynamic>> _post(String path, Map<String, dynamic> body) async {
    final res = await http
        .post(
          Uri.parse('$baseUrl$path'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode(body),
        )
        .timeout(const Duration(seconds: 12));
    if (res.statusCode >= 400) {
      throw Exception('서버 오류 (${res.statusCode}): ${res.body}');
    }
    return jsonDecode(utf8.decode(res.bodyBytes)) as Map<String, dynamic>;
  }

  Future<Map<String, dynamic>> analyze(Profile profile) =>
      _post('/api/saju/analyze', profile.toJson());

  Future<Map<String, dynamic>> today(Profile profile) =>
      _post('/api/fortune/today', profile.toJson());

  Future<Map<String, dynamic>> theme(Profile profile, String theme) =>
      _post('/api/fortune/theme', profile.toJson(theme: theme));

  Future<Map<String, dynamic>> period(Profile profile, String period) =>
      _post('/api/fortune/period', profile.toJson(period: period));

  Future<Map<String, dynamic>> saveProfile(Profile profile) =>
      _post('/api/profile', profile.toJson());
}
