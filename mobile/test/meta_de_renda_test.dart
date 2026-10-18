import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:fiance/core/models.dart';
import 'package:fiance/core/theme.dart';
import 'package:fiance/features/patrimony/widgets/income_goal.dart';

void main() {
  testWidgets('o progresso da meta chega em percentual e não é multiplicado de novo', (
    tester,
  ) async {
    await tester.pumpWidget(
      MaterialApp(
        theme: buildAppTheme(Brightness.light),
        home: Scaffold(
          body: SingleChildScrollView(
            child: FiIncomeGoalBlock(
              summary: DashboardSummary(
                totalInvested: 84200,
                totalCurrent: 97430.55,
                totalPnl: 13230.55,
                totalPnlPct: 15.71,
                monthlyDividendsEstimate: 412.8,
                passiveIncomeGoal: 5000,
                passiveIncomeProgress: 8.26,
                positionsCount: 6,
              ),
            ),
          ),
        ),
      ),
    );

    expect(
      find.textContaining('8% do alvo'),
      findsOneWidget,
      reason: 'R\$ 412,80 de R\$ 5.000,00 é 8%; o app já mostrou 826%',
    );
  });
}
