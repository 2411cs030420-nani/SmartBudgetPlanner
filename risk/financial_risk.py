def detect_financial_risk(
    expense_ratio,
    savings_rate,
    monthly_change,
    predicted_expense=0,
    total_income=0
):
    """
    Detect financial risk using:
    1. Current expense-to-income ratio
    2. Savings rate
    3. Monthly spending trend
    4. Predicted next-month expense
    """

    # Convert values safely to numbers
    expense_ratio = float(expense_ratio or 0)
    savings_rate = float(savings_rate or 0)
    monthly_change = float(monthly_change or 0)
    predicted_expense = float(predicted_expense or 0)
    total_income = float(total_income or 0)

    # ---------------------------------
    # 1. Current Expense Ratio Risk
    # Maximum: 40 points
    # ---------------------------------

    if expense_ratio <= 50:
        expense_risk = 0
    elif expense_ratio <= 70:
        expense_risk = 15
    elif expense_ratio <= 90:
        expense_risk = 30
    else:
        expense_risk = 40

    # ---------------------------------
    # 2. Savings Rate Risk
    # Maximum: 30 points
    # ---------------------------------

    if savings_rate >= 20:
        savings_risk = 0
    elif savings_rate >= 10:
        savings_risk = 10
    elif savings_rate >= 0:
        savings_risk = 20
    else:
        savings_risk = 30

    # ---------------------------------
    # 3. Spending Trend Risk
    # Maximum: 15 points
    # ---------------------------------

    if monthly_change <= 10:
        trend_risk = 0
    elif monthly_change <= 25:
        trend_risk = 5
    elif monthly_change <= 50:
        trend_risk = 10
    else:
        trend_risk = 15

    # ---------------------------------
    # 4. Predicted Expense Risk
    # Maximum: 15 points
    # ---------------------------------

    if total_income > 0:

        predicted_expense_ratio = (
            predicted_expense / total_income
        ) * 100

        if predicted_expense_ratio <= 50:
            prediction_risk = 0
        elif predicted_expense_ratio <= 70:
            prediction_risk = 5
        elif predicted_expense_ratio <= 90:
            prediction_risk = 10
        else:
            prediction_risk = 15

    else:
        predicted_expense_ratio = 0
        prediction_risk = 0

    # ---------------------------------
    # Total Risk Score
    # ---------------------------------

    risk_score = (
        expense_risk
        + savings_risk
        + trend_risk
        + prediction_risk
    )

    risk_score = min(max(risk_score, 0), 100)

    # ---------------------------------
    # Risk Level
    # ---------------------------------

    if risk_score >= 75:
        risk_level = "Critical"

        risk_message = (
            "Your financial risk is critical. "
            "Expenses are placing significant pressure "
            "on your income. Immediate spending reduction "
            "and budget adjustments are recommended."
        )

    elif risk_score >= 50:
        risk_level = "High"

        risk_message = (
            "Your financial risk is high. "
            "Your current spending pattern may make it "
            "difficult to maintain financial stability."
        )

    elif risk_score >= 25:
        risk_level = "Moderate"

        risk_message = (
            "Your financial risk is moderate. "
            "Your finances are manageable, but some "
            "spending adjustments could improve stability."
        )

    else:
        risk_level = "Low"

        risk_message = (
            "Your financial risk is low. "
            "Your current spending pattern appears "
            "relatively manageable."
        )

    # ---------------------------------
    # Return Results
    # ---------------------------------

    return {
        "risk_score": round(risk_score, 2),
        "risk_level": risk_level,
        "risk_message": risk_message,
        "predicted_expense_ratio": round(
            predicted_expense_ratio, 2
        )
    }