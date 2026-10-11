import pandas as pd
from sklearn.linear_model import LinearRegression


def predict_next_month_expense(monthly_expenses):
    """
    Predict the next month's expense using historical
    monthly expense data.

    monthly_expenses should contain dictionaries like:

    [
        {"month": "2026-01", "total": 25000},
        {"month": "2026-02", "total": 28000}
    ]
    """

    # --------------------------------
    # CHECK DATA
    # --------------------------------

    if not monthly_expenses:
        return {
            "prediction": 0,
            "average_expense": 0,
            "change_percentage": 0,
            "status": "No Data",
            "message": "There is not enough expense data for prediction."
        }

    # --------------------------------
    # CREATE DATAFRAME
    # --------------------------------

    data = pd.DataFrame(monthly_expenses)

    data["total"] = pd.to_numeric(
        data["total"],
        errors="coerce"
    )

    data = data.dropna(subset=["total"])

    # --------------------------------
    # CHECK VALID DATA
    # --------------------------------

    if data.empty:
        return {
            "prediction": 0,
            "average_expense": 0,
            "change_percentage": 0,
            "status": "No Data",
            "message": "There is not enough valid expense data for prediction."
        }

    # --------------------------------
    # AVERAGE EXPENSE
    # --------------------------------

    average_expense = float(
        data["total"].mean()
    )

    # --------------------------------
    # FALLBACK FOR LIMITED DATA
    # --------------------------------
    # ML prediction is not reliable with
    # very little historical information.

    if len(data) < 3:

        prediction = average_expense

        change_percentage = 0

        return {
            "prediction": round(prediction, 2),
            "average_expense": round(average_expense, 2),
            "change_percentage": round(change_percentage, 2),
            "status": "Baseline",
            "message": (
                "More historical monthly data is needed "
                "for a reliable ML prediction. "
                "The current prediction uses your average spending."
            )
        }

    # --------------------------------
    # PREPARE ML DATA
    # --------------------------------

    data = data.reset_index(drop=True)

    data["month_number"] = range(
        1,
        len(data) + 1
    )

    X = data[["month_number"]]

    y = data["total"]

    # --------------------------------
    # TRAIN ML MODEL
    # --------------------------------

    model = LinearRegression()

    model.fit(X, y)

    # --------------------------------
    # PREDICT NEXT MONTH
    # --------------------------------

    next_month_number = len(data) + 1

    prediction = model.predict(
        [[next_month_number]]
    )[0]

    prediction = max(
        float(prediction),
        0
    )

    # --------------------------------
    # COMPARE WITH AVERAGE
    # --------------------------------

    if average_expense > 0:

        change_percentage = (
            (prediction - average_expense)
            / average_expense
        ) * 100

    else:

        change_percentage = 0

    # --------------------------------
    # PREDICTION STATUS
    # --------------------------------

    if change_percentage > 10:

        status = "Increasing"

        message = (
            "Your predicted expenses are higher than "
            "your historical average. Consider reviewing "
            "your spending before the next month."
        )

    elif change_percentage < -10:

        status = "Decreasing"

        message = (
            "Your predicted expenses are lower than "
            "your historical average. Your spending "
            "trend appears to be improving."
        )

    else:

        status = "Stable"

        message = (
            "Your predicted expenses are close to "
            "your historical average."
        )

    # --------------------------------
    # RETURN RESULT
    # --------------------------------

    return {
        "prediction": round(prediction, 2),
        "average_expense": round(average_expense, 2),
        "change_percentage": round(change_percentage, 2),
        "status": status,
        "message": message
    }