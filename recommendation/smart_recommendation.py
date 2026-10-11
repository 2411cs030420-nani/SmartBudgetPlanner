def generate_smart_recommendation(
    expense_ratio,
    savings_rate,
    monthly_change,
    highest_category,
    highest_category_percentage,
    risk_level
):
    """
    Generate personalized financial recommendations
    based on the user's financial behavior.
    """

    recommendations = []

    # -------------------------------
    # 1. Expense Ratio
    # -------------------------------

    if expense_ratio > 90:

        recommendations.append(
            "Your expenses are very high compared with "
            "your income. Focus on reducing non-essential "
            "expenses immediately."
        )

    elif expense_ratio > 70:

        recommendations.append(
            "Your expense level is high. Review your "
            "non-essential spending and try to reduce it."
        )

    elif expense_ratio > 50:

        recommendations.append(
            "Your spending is moderate. Try to keep "
            "expenses below 50% of your income where possible."
        )


    # -------------------------------
    # 2. Savings Rate
    # -------------------------------

    if savings_rate < 10:

        recommendations.append(
            "Your savings rate is low. Try to build a "
            "regular savings habit."
        )

    elif savings_rate < 20:

        recommendations.append(
            "Your savings are improving, but aim to "
            "increase your savings rate gradually."
        )

    elif savings_rate >= 30:

        recommendations.append(
            "You are maintaining a strong savings rate. "
            "Continue this financial discipline."
        )


    # -------------------------------
    # 3. Monthly Spending Trend
    # -------------------------------

    if monthly_change > 25:

        recommendations.append(
            "Your monthly spending has increased significantly. "
            "Review recent expenses to identify the reason."
        )

    elif monthly_change > 10:

        recommendations.append(
            "Your spending is increasing. Monitor your "
            "next month's expenses carefully."
        )

    elif monthly_change < -10:

        recommendations.append(
            "Your spending has decreased compared with "
            "the previous month. Continue monitoring this trend."
        )


    # -------------------------------
    # 4. Highest Spending Category
    # -------------------------------

    if highest_category_percentage > 50:

        recommendations.append(
            f"{highest_category} represents more than half "
            "of your total spending. Consider setting a "
            "specific budget limit for this category."
        )

    elif highest_category_percentage > 30:

        recommendations.append(
            f"{highest_category} is your largest spending "
            "category. Monitor this category closely."
        )


    # -------------------------------
    # 5. Financial Risk
    # -------------------------------

    if risk_level == "Critical":

        recommendations.append(
            "Your financial risk is critical. Prioritize "
            "essential expenses and reduce unnecessary spending."
        )

    elif risk_level == "High":

        recommendations.append(
            "Your financial risk is high. Review your "
            "spending pattern and strengthen your savings."
        )

    elif risk_level == "Moderate":

        recommendations.append(
            "Your financial risk is moderate. Small spending "
            "adjustments can improve your financial stability."
        )

    elif risk_level == "Low":

        recommendations.append(
            "Your financial risk is currently low. "
            "Continue maintaining your current financial habits."
        )


    # -------------------------------
    # Default Recommendation
    # -------------------------------

    if not recommendations:

        recommendations.append(
            "Your financial behavior looks balanced. "
            "Continue tracking your income and expenses regularly."
        )


    return recommendations