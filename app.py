from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
from flask_bcrypt import Bcrypt
from prediction.expense_prediction import predict_next_month_expense
from risk.financial_risk import detect_financial_risk
from recommendation.smart_recommendation import generate_smart_recommendation

app = Flask(__name__)

app.secret_key = "smart-budget-planner-secret-key"

bcrypt = Bcrypt(app)


def get_db_connection():
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="12345678",
        database="smart_budget_planner"
    )
    return connection

@app.route("/")
def home():

    if "user_id" in session:
        return redirect(url_for("dashboard"))

    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
            (name, email, hashed_password)
        )

        connection.commit()

        cursor.close()
        connection.close()

        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM users WHERE email = %s",
            (email,)
        )

        user = cursor.fetchone()

        cursor.close()
        connection.close()

        if user and bcrypt.check_password_hash(user["password"], password):

            session["user_id"] = user["id"]
            session["user_name"] = user["name"]

            return redirect(url_for("dashboard"))

        return "Invalid email or password"

    return render_template("login.html")


@app.route("/income", methods=["GET", "POST"])
def income():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        amount = request.form["amount"]
        source = request.form["source"]
        date = request.form["date"]
        description = request.form["description"]

        user_id = session["user_id"]

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO income
            (user_id, amount, source, date, description)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (user_id, amount, source, date, description)
        )

        connection.commit()

        cursor.close()
        connection.close()

        return redirect(url_for("dashboard"))

    return render_template("income.html")


@app.route("/expense", methods=["GET", "POST"])
def expense():

    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":

        amount = request.form["amount"]
        category = request.form["category"]
        date = request.form["date"]
        payment_method = request.form["payment_method"]
        description = request.form["description"]

        user_id = session["user_id"]

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT INTO expenses
            (user_id, amount, category, date, payment_method, description)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                user_id,
                amount,
                category,
                date,
                payment_method,
                description
            )
        )

        connection.commit()

        cursor.close()
        connection.close()

        return redirect(url_for("dashboard"))

    return render_template("expense.html")


@app.route("/transactions")
def transactions():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT id, amount, source, date, description
        FROM income
        WHERE user_id = %s
        ORDER BY date DESC
        """,
        (user_id,)
    )

    incomes = cursor.fetchall()

    cursor.execute(
        """
        SELECT id, amount, category, date, payment_method, description
        FROM expenses
        WHERE user_id = %s
        ORDER BY date DESC
        """,
        (user_id,)
    )

    expenses = cursor.fetchall()

    cursor.close()
    connection.close()

    return render_template(
        "transactions.html",
        incomes=incomes,
        expenses=expenses
    )


@app.route("/delete_income/<int:income_id>")
def delete_income(income_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM income
        WHERE id = %s AND user_id = %s
        """,
        (income_id, user_id)
    )

    connection.commit()

    cursor.close()
    connection.close()

    return redirect(url_for("transactions"))


@app.route("/delete_expense/<int:expense_id>")
def delete_expense(expense_id):

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        DELETE FROM expenses
        WHERE id = %s AND user_id = %s
        """,
        (expense_id, user_id)
    )

    connection.commit()

    cursor.close()
    connection.close()

    return redirect(url_for("transactions"))


@app.route("/analytics")
def analytics():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # --------------------------------
    # CATEGORY-WISE EXPENSES
    # --------------------------------

    cursor.execute(
        """
        SELECT category, SUM(amount) AS total
        FROM expenses
        WHERE user_id = %s
        GROUP BY category
        ORDER BY total DESC
        """,
        (user_id,)
    )

    category_expenses = cursor.fetchall()


    # --------------------------------
    # MONTHLY EXPENSES
    # --------------------------------

    cursor.execute(
        """
        SELECT
            DATE_FORMAT(`date`, '%Y-%m') AS month,
            SUM(amount) AS total
        FROM expenses
        WHERE user_id = %s
        GROUP BY DATE_FORMAT(`date`, '%Y-%m')
        ORDER BY month ASC
        """,
        (user_id,)
    )

    monthly_expenses = cursor.fetchall()


    # --------------------------------
    # FUTURE EXPENSE PREDICTION
    # --------------------------------

    prediction_result = predict_next_month_expense(
        monthly_expenses
    )

    predicted_expense = prediction_result["prediction"]
    average_expense = prediction_result["average_expense"]
    prediction_change = prediction_result["change_percentage"]
    prediction_status = prediction_result["status"]
    prediction_message = prediction_result["message"]


    # --------------------------------
    # TOTAL EXPENSES
    # --------------------------------

    cursor.execute(
        """
        SELECT COALESCE(SUM(amount), 0) AS total
        FROM expenses
        WHERE user_id = %s
        """,
        (user_id,)
    )

    total_expenses = cursor.fetchone()["total"]


    # --------------------------------
    # TOTAL INCOME
    # --------------------------------

    cursor.execute(
        """
        SELECT COALESCE(SUM(amount), 0) AS total
        FROM income
        WHERE user_id = %s
        """,
        (user_id,)
    )

    total_income = cursor.fetchone()["total"]


    cursor.close()
    connection.close()


    # --------------------------------
    # BASIC FINANCIAL CALCULATIONS
    # --------------------------------

    total_savings = total_income - total_expenses


    if total_income > 0:
        savings_rate = (total_savings / total_income) * 100
        expense_ratio = (total_expenses / total_income) * 100
    else:
        savings_rate = 0
        expense_ratio = 0


    # --------------------------------
    # FINANCIAL HEALTH SCORE
    # --------------------------------

    health_score = 0


    # Savings component - 50 points
    savings_score = min(max(savings_rate, 0), 50)


    # Expense ratio component - 30 points
    if expense_ratio <= 50:
        expense_score = 30

    elif expense_ratio <= 70:
        expense_score = 20

    elif expense_ratio <= 90:
        expense_score = 10

    else:
        expense_score = 0


    # Spending concentration component - 20 points
    if category_expenses and total_expenses > 0:

        highest_category = float(category_expenses[0]["total"])

        concentration = (
            highest_category / float(total_expenses)
        ) * 100

        if concentration <= 40:
            concentration_score = 20

        elif concentration <= 60:
            concentration_score = 15

        elif concentration <= 80:
            concentration_score = 10

        else:
            concentration_score = 5

    else:

        concentration = 0
        concentration_score = 20


    health_score = round(
        savings_score +
        expense_score +
        concentration_score
    )


    # Make sure score stays between 0 and 100
    health_score = max(0, min(100, health_score))


    # --------------------------------
    # SPENDING BEHAVIOR ANALYSIS
    # --------------------------------

    # Highest spending category
    if category_expenses and total_expenses > 0:

        highest_category = category_expenses[0]["category"]
        highest_category_amount = category_expenses[0]["total"]

        highest_category_percentage = (
            float(highest_category_amount)
            / float(total_expenses)
        ) * 100

    else:

        highest_category = "No data"
        highest_category_amount = 0
        highest_category_percentage = 0


    # --------------------------------
    # MONTHLY SPENDING TREND
    # --------------------------------

    if len(monthly_expenses) >= 2:

        previous_month = float(
            monthly_expenses[-2]["total"]
        )

        current_month = float(
            monthly_expenses[-1]["total"]
        )

        if previous_month > 0:

            monthly_change = (
                (current_month - previous_month)
                / previous_month
            ) * 100

        else:

            monthly_change = 0

    else:

        monthly_change = 0

    # --------------------------------
# FINANCIAL RISK DETECTION
# --------------------------------

    risk_result = detect_financial_risk(
    expense_ratio=expense_ratio,
    savings_rate=savings_rate,
    monthly_change=monthly_change,
    predicted_expense=predicted_expense,
    total_income=total_income
)

    risk_score = risk_result["risk_score"]
    risk_level = risk_result["risk_level"]
    risk_message = risk_result["risk_message"]
    predicted_expense_ratio = risk_result["predicted_expense_ratio"]



    # --------------------------------
# SMART RECOMMENDATIONS
# --------------------------------

    smart_recommendations = generate_smart_recommendation(
        expense_ratio=expense_ratio,
        savings_rate=savings_rate,
        monthly_change=monthly_change,
        highest_category=highest_category,
        highest_category_percentage=highest_category_percentage,
        risk_level=risk_level
    )
    # --------------------------------
    # SPENDING STATUS
    # --------------------------------

    if expense_ratio > 90:

        spending_status = "Critical"

        spending_message = (
            "Your expenses are consuming most of your income. "
            "Immediate spending control is recommended."
        )

    elif expense_ratio > 70:

        spending_status = "High"

        spending_message = (
            "Your spending level is relatively high compared "
            "with your income."
        )

    elif expense_ratio > 50:

        spending_status = "Moderate"

        spending_message = (
            "Your spending is manageable, but increasing your "
            "savings margin would improve financial stability."
        )

    else:

        spending_status = "Healthy"

        spending_message = (
            "Your expenses are currently within a healthy "
            "range compared with your income."
        )


    # --------------------------------
    # TREND MESSAGE
    # --------------------------------

    if monthly_change > 10:

        trend_message = (
            f"Your spending increased by "
            f"{monthly_change:.1f}% compared with the previous month."
        )

    elif monthly_change < -10:

        trend_message = (
            f"Your spending decreased by "
            f"{abs(monthly_change):.1f}% compared with the previous month."
        )

    else:

        trend_message = (
            "Your monthly spending is relatively stable."
        )

    risk_result = detect_financial_risk(
    expense_ratio=expense_ratio,
    savings_rate=savings_rate,
    monthly_change=monthly_change,
    predicted_expense=predicted_expense,
    total_income=total_income
)

    risk_score = risk_result["risk_score"]
    risk_level = risk_result["risk_level"]
    risk_message = risk_result["risk_message"]
    predicted_expense_ratio = risk_result["predicted_expense_ratio"]
    # --------------------------------
    # SMART RECOMMENDATION
    # --------------------------------

    if expense_ratio > 70:

        recommendation = (
            "Consider reducing non-essential expenses "
            "and increasing your savings margin."
        )

    elif savings_rate < 20:

        recommendation = (
            "Try to build a stronger savings habit by "
            "setting aside at least 20% of your income."
        )

    elif highest_category_percentage > 50:

        recommendation = (
            f"{highest_category} represents a large portion "
            "of your total spending. Consider setting a budget "
            "limit for this category."
        )

    else:

        recommendation = (
            "Your spending pattern looks balanced. "
            "Continue maintaining your current savings discipline."
        )


    # --------------------------------
    # HEALTH STATUS
    # --------------------------------

    if health_score >= 80:

        health_status = "Excellent"

        health_message = (
            "Your financial pattern is strong. "
            "You are maintaining healthy savings and spending levels."
        )

    elif health_score >= 60:

        health_status = "Healthy"

        health_message = (
            "Your finances are generally healthy, "
            "but there is room to improve your spending efficiency."
        )

    elif health_score >= 40:

        health_status = "Moderate"

        health_message = (
            "Your finances need attention. "
            "Try to increase savings and control unnecessary expenses."
        )

    else:

        health_status = "At Risk"

        health_message = (
            "Your current spending pattern may create financial pressure. "
            "Reducing unnecessary expenses should be a priority."
        )


    # --------------------------------
    # RENDER ANALYTICS
    # --------------------------------

    return render_template(
        "analytics.html",

        category_expenses=category_expenses,
        monthly_expenses=monthly_expenses,

        total_expenses=total_expenses,
        total_income=total_income,
        total_savings=total_savings,

        savings_rate=savings_rate,
        expense_ratio=expense_ratio,

        health_score=health_score,
        health_status=health_status,
        health_message=health_message,

        concentration=concentration,

        highest_category=highest_category,
        highest_category_amount=highest_category_amount,
        highest_category_percentage=highest_category_percentage,

        monthly_change=monthly_change,

        spending_status=spending_status,
        spending_message=spending_message,

        trend_message=trend_message,

        recommendation=recommendation,

        predicted_expense=predicted_expense,
        average_expense=average_expense,
        prediction_change=prediction_change,
        prediction_status=prediction_status,
        prediction_message=prediction_message,

       

        risk_score=risk_score,
        risk_level=risk_level,
        risk_message=risk_message,
        predicted_expense_ratio=predicted_expense_ratio,
        smart_recommendations=smart_recommendations
        )
@app.route("/budget", methods=["GET", "POST"])
def budget():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    if request.method == "POST":

        category = request.form["category"]
        amount = request.form["amount"]
        month = request.form["month"]

        year = int(month.split("-")[0])
        month_number = int(month.split("-")[1])

        cursor.execute(
            """
            INSERT INTO budgets
            (user_id, category, amount, month, year)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                user_id,
                category,
                amount,
                month_number,
                year
            )
        )

        connection.commit()

    # --------------------------------
    # BUDGET VS ACTUAL SPENDING
    # --------------------------------

    cursor.execute(
        """
        SELECT
            b.id,
            b.category,
            b.amount AS budget_amount,
            b.month,
            b.year,
            COALESCE(SUM(e.amount), 0) AS actual_expense

        FROM budgets b

        LEFT JOIN expenses e
            ON e.user_id = b.user_id
            AND e.category = b.category
            AND MONTH(e.date) = b.month
            AND YEAR(e.date) = b.year

        WHERE b.user_id = %s

        GROUP BY
            b.id,
            b.category,
            b.amount,
            b.month,
            b.year

        ORDER BY
            b.year DESC,
            b.month DESC,
            b.id DESC
        """,
        (user_id,)
    )

    budgets = cursor.fetchall()

    # Calculate remaining amount and usage
    for item in budgets:

        item["remaining"] = (
            float(item["budget_amount"])
            - float(item["actual_expense"])
        )

        if float(item["budget_amount"]) > 0:
            item["usage_percentage"] = (
                float(item["actual_expense"])
                / float(item["budget_amount"])
            ) * 100
        else:
            item["usage_percentage"] = 0

    cursor.close()
    connection.close()

    return render_template(
        "budget.html",
        budgets=budgets
    )
@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # ==========================================
    # TOTAL INCOME
    # ==========================================

    cursor.execute(
        """
        SELECT COALESCE(SUM(amount), 0) AS total_income
        FROM income
        WHERE user_id = %s
        """,
        (user_id,)
    )

    total_income = float(
        cursor.fetchone()["total_income"] or 0
    )


    # ==========================================
    # TOTAL EXPENSES
    # ==========================================

    cursor.execute(
        """
        SELECT COALESCE(SUM(amount), 0) AS total_expenses
        FROM expenses
        WHERE user_id = %s
        """,
        (user_id,)
    )

    total_expenses = float(
        cursor.fetchone()["total_expenses"] or 0
    )


    # ==========================================
    # TOTAL SAVINGS
    # ==========================================

    total_savings = total_income - total_expenses


    # ==========================================
    # FINANCIAL HEALTH
    # ==========================================

    if total_income > 0:

        savings_rate = (
            total_savings / total_income
        ) * 100

        expense_ratio = (
            total_expenses / total_income
        ) * 100

    else:

        savings_rate = 0
        expense_ratio = 0


    savings_score = min(
        max(savings_rate, 0),
        50
    )


    if expense_ratio <= 50:
        expense_score = 30

    elif expense_ratio <= 70:
        expense_score = 20

    elif expense_ratio <= 90:
        expense_score = 10

    else:
        expense_score = 0


    health_score = round(
        savings_score + expense_score
    )

    health_score = max(
        0,
        min(100, health_score)
    )


    # ==========================================
    # CURRENT MONTH INCOME
    # ==========================================

    cursor.execute(
        """
        SELECT COALESCE(SUM(amount), 0) AS monthly_income
        FROM income
        WHERE user_id = %s
        AND MONTH(date) = MONTH(CURDATE())
        AND YEAR(date) = YEAR(CURDATE())
        """,
        (user_id,)
    )

    monthly_income = float(
        cursor.fetchone()["monthly_income"] or 0
    )


    # ==========================================
    # CURRENT MONTH EXPENSES
    # ==========================================

    cursor.execute(
        """
        SELECT COALESCE(SUM(amount), 0) AS monthly_expenses
        FROM expenses
        WHERE user_id = %s
        AND MONTH(date) = MONTH(CURDATE())
        AND YEAR(date) = YEAR(CURDATE())
        """,
        (user_id,)
    )

    monthly_expenses = float(
        cursor.fetchone()["monthly_expenses"] or 0
    )


    monthly_savings = (
        monthly_income - monthly_expenses
    )


    if monthly_income > 0:

        monthly_savings_rate = (
            monthly_savings / monthly_income
        ) * 100

    else:

        monthly_savings_rate = 0


    # ==========================================
    # CURRENT MONTH BUDGET
    # ==========================================

    cursor.execute(
        """
        SELECT COALESCE(SUM(amount), 0) AS budget_amount
        FROM budgets
        WHERE user_id = %s
        AND month = MONTH(CURDATE())
        AND year = YEAR(CURDATE())
        """,
        (user_id,)
    )

    current_budget = float(
        cursor.fetchone()["budget_amount"] or 0
    )


    cursor.execute(
        """
        SELECT COALESCE(SUM(amount), 0) AS actual_expense
        FROM expenses
        WHERE user_id = %s
        AND MONTH(date) = MONTH(CURDATE())
        AND YEAR(date) = YEAR(CURDATE())
        """,
        (user_id,)
    )

    current_actual = float(
        cursor.fetchone()["actual_expense"] or 0
    )


    budget_remaining = (
        current_budget - current_actual
    )


    if current_budget > 0:

        budget_usage = (
            current_actual / current_budget
        ) * 100

    else:

        budget_usage = 0


    # ==========================================
    # BUDGET STATUS
    # ==========================================

    if current_budget <= 0:

        budget_status = "No Budget Set"

    elif budget_usage > 100:

        budget_status = "Budget Exceeded"

    elif budget_usage >= 70:

        budget_status = "Near Budget Limit"

    else:

        budget_status = "Within Budget"


    # ==========================================
    # CATEGORY BUDGETS
    # ==========================================

    cursor.execute(
        """
        SELECT
            b.id,
            b.category,
            b.amount AS budget_amount,
            COALESCE(SUM(e.amount), 0) AS actual_expense

        FROM budgets b

        LEFT JOIN expenses e
            ON e.user_id = b.user_id
            AND e.category = b.category
            AND MONTH(e.date) = b.month
            AND YEAR(e.date) = b.year

        WHERE b.user_id = %s
        AND b.month = MONTH(CURDATE())
        AND b.year = YEAR(CURDATE())

        GROUP BY
            b.id,
            b.category,
            b.amount

        ORDER BY b.category
        """,
        (user_id,)
    )

    category_budgets = cursor.fetchall()


    for item in category_budgets:

        item["budget_amount"] = float(
            item["budget_amount"] or 0
        )

        item["actual_expense"] = float(
            item["actual_expense"] or 0
        )

        item["remaining"] = (
            item["budget_amount"]
            - item["actual_expense"]
        )

        if item["budget_amount"] > 0:

            item["usage_percentage"] = (
                item["actual_expense"]
                / item["budget_amount"]
            ) * 100

        else:

            item["usage_percentage"] = 0


    # ==========================================
    # BUDGET ALERTS
    # ==========================================

    budget_alerts = []

    for item in category_budgets:

        if item["usage_percentage"] > 100:

            budget_alerts.append({
                "category": item["category"],
                "level": "danger",
                "message": (
                    f"{item['category']} budget "
                    "has been exceeded."
                )
            })

        elif item["usage_percentage"] >= 70:

            budget_alerts.append({
                "category": item["category"],
                "level": "warning",
                "message": (
                    f"{item['category']} is close "
                    "to its budget limit."
                )
            })


    # ==========================================
    # FINANCIAL GOALS
    # ==========================================

    cursor.execute(
        """
        SELECT
            id,
            goal_name,
            target_amount,
            saved_amount

        FROM financial_goals

        WHERE user_id = %s

        ORDER BY id DESC
        """,
        (user_id,)
    )

    goals = cursor.fetchall()


    for goal in goals:

        target = float(
            goal["target_amount"] or 0
        )

        saved = float(
            goal["saved_amount"] or 0
        )

        if target > 0:

            goal["progress"] = min(
                (saved / target) * 100,
                100
            )

        else:

            goal["progress"] = 0


    # ==========================================
    # GOAL SUMMARY
    # ==========================================

    total_goal_target = sum(
        float(goal["target_amount"] or 0)
        for goal in goals
    )

    total_goal_saved = sum(
        float(goal["saved_amount"] or 0)
        for goal in goals
    )


    if total_goal_target > 0:

        overall_goal_progress = (
            total_goal_saved /
            total_goal_target
        ) * 100

    else:

        overall_goal_progress = 0


    # ==========================================
    # INTELLIGENCE MESSAGE
    # ==========================================

    if health_score >= 80:

        financial_status = "Strong"

    elif health_score >= 60:

        financial_status = "Moderate"

    elif health_score >= 40:

        financial_status = "Needs Attention"

    else:

        financial_status = "High Attention"


    if budget_status == "Budget Exceeded":

        financial_action = (
            "Review your spending and reduce "
            "non-essential expenses."
        )

    elif monthly_savings <= 0:

        financial_action = (
            "Your current monthly spending is "
            "equal to or higher than your income."
        )

    elif budget_status == "Near Budget Limit":

        financial_action = (
            "You are approaching your monthly "
            "budget limit."
        )

    elif goals and overall_goal_progress < 50:

        financial_action = (
            "Increase your monthly savings to "
            "reach your financial goals faster."
        )

    else:

        financial_action = (
            "Continue tracking your spending "
            "and maintaining your savings."
        )


    cursor.close()
    connection.close()


    return render_template(
        "dashboard.html",

        user_name=session["user_name"],

        total_income=total_income,
        total_expenses=total_expenses,
        total_savings=total_savings,

        savings_rate=savings_rate,
        expense_ratio=expense_ratio,
        health_score=health_score,

        monthly_income=monthly_income,
        monthly_expenses=monthly_expenses,
        monthly_savings=monthly_savings,
        monthly_savings_rate=monthly_savings_rate,

        current_budget=current_budget,
        current_actual=current_actual,
        budget_remaining=budget_remaining,
        budget_usage=budget_usage,
        budget_status=budget_status,

        category_budgets=category_budgets,
        budget_alerts=budget_alerts,

        goals=goals,
        total_goal_target=total_goal_target,
        total_goal_saved=total_goal_saved,
        overall_goal_progress=overall_goal_progress,

        financial_status=financial_status,
        financial_action=financial_action
    )
# FINANCIAL GOALS + GOAL INTELLIGENCE
# ==========================================

@app.route("/goals", methods=["GET", "POST"])
def goals():

    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    # --------------------------------------
    # ADD / UPDATE / DELETE GOAL
    # --------------------------------------

    if request.method == "POST":

        action = request.form.get("action")


        # ADD GOAL
        if action == "add":

            goal_name = request.form["goal_name"]

            target_amount = float(
                request.form["target_amount"]
            )

            cursor.execute(
                """
                INSERT INTO financial_goals
                (
                    user_id,
                    goal_name,
                    target_amount,
                    saved_amount
                )
                VALUES (%s, %s, %s, %s)
                """,
                (
                    user_id,
                    goal_name,
                    target_amount,
                    0
                )
            )

            connection.commit()


        # UPDATE SAVED AMOUNT
        elif action == "update":

            goal_id = request.form["goal_id"]

            saved_amount = float(
                request.form["saved_amount"]
            )

            cursor.execute(
                """
                UPDATE financial_goals

                SET saved_amount = %s

                WHERE id = %s
                AND user_id = %s
                """,
                (
                    saved_amount,
                    goal_id,
                    user_id
                )
            )

            connection.commit()


        # DELETE GOAL
        elif action == "delete":

            goal_id = request.form["goal_id"]

            cursor.execute(
                """
                DELETE FROM financial_goals

                WHERE id = %s
                AND user_id = %s
                """,
                (
                    goal_id,
                    user_id
                )
            )

            connection.commit()


    # --------------------------------------
    # CURRENT MONTH SAVINGS
    # --------------------------------------

    cursor.execute(
        """
        SELECT
            COALESCE(SUM(amount), 0) AS monthly_income
        FROM income
        WHERE user_id = %s
        AND MONTH(date) = MONTH(CURDATE())
        AND YEAR(date) = YEAR(CURDATE())
        """,
        (user_id,)
    )

    monthly_income = float(
        cursor.fetchone()["monthly_income"] or 0
    )


    cursor.execute(
        """
        SELECT
            COALESCE(SUM(amount), 0) AS monthly_expenses
        FROM expenses
        WHERE user_id = %s
        AND MONTH(date) = MONTH(CURDATE())
        AND YEAR(date) = YEAR(CURDATE())
        """,
        (user_id,)
    )

    monthly_expenses = float(
        cursor.fetchone()["monthly_expenses"] or 0
    )


    monthly_savings = (
        monthly_income - monthly_expenses
    )


    # --------------------------------------
    # GET GOALS
    # --------------------------------------

    cursor.execute(
        """
        SELECT
            id,
            goal_name,
            target_amount,
            saved_amount,
            created_at

        FROM financial_goals

        WHERE user_id = %s

        ORDER BY id DESC
        """,
        (user_id,)
    )

    goals_list = cursor.fetchall()


    # --------------------------------------
    # GOAL INTELLIGENCE
    # --------------------------------------

    for goal in goals_list:

        target = float(
            goal["target_amount"] or 0
        )

        saved = float(
            goal["saved_amount"] or 0
        )


        # Remaining amount

        goal["remaining"] = max(
            target - saved,
            0
        )


        # Progress percentage

        if target > 0:

            goal["progress"] = min(
                (saved / target) * 100,
                100
            )

        else:

            goal["progress"] = 0


        # ----------------------------------
        # ESTIMATED MONTHS
        # ----------------------------------

        if goal["remaining"] <= 0:

            goal["estimated_months"] = 0

            goal["goal_status"] = "Completed"

            goal["goal_message"] = (
                "🎉 Goal achieved!"
            )


        elif monthly_savings > 0:

            estimated_months = (
                goal["remaining"]
                / monthly_savings
            )

            goal["estimated_months"] = max(
                1,
                int(estimated_months + 0.9999)
            )

            goal["goal_status"] = "On Track"

            goal["goal_message"] = (
                f"At your current monthly savings "
                f"of ₹{monthly_savings:.0f}, "
                f"you may reach this goal in about "
                f"{goal['estimated_months']} month(s)."
            )


        else:

            goal["estimated_months"] = None

            goal["goal_status"] = "Needs Attention"

            goal["goal_message"] = (
                "Your current monthly savings "
                "are not positive, so a completion "
                "time cannot be estimated yet."
            )


    cursor.close()
    connection.close()


    return render_template(
        "goals.html",

        goals=goals_list,

        monthly_income=monthly_income,

        monthly_expenses=monthly_expenses,

        monthly_savings=monthly_savings
    )
@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("login"))

if __name__ == "__main__":

    import webbrowser
    from threading import Timer

    url = "http://127.0.0.1:5000/"

    Timer(
        1,
        lambda: webbrowser.open(url)
    ).start()

    app.run(debug=True)