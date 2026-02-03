from datetime import date
from django.db.models import Sum
from api.models import Loan, Customer

def calculate_credit_score(customer_id: int):
    """
    Calculates a credit score (0-100) based on assignment criteria.
    """
    try:
        customer = Customer.objects.get(customer_id=customer_id)
    except Customer.DoesNotExist:
        return 0, "Customer not found"

    loans = Loan.objects.filter(customer_id=customer)
    total_loans = loans.count()

    # Rule (v): Sum of current loans > Approved Limit
    total_loan_amount = loans.aggregate(Sum("loan_amount"))["loan_amount__sum"] or 0
    if total_loan_amount > customer.approved_limit:
        return 0, "Total debt exceeds approved limit"

    # Rule: New customers with no history start with a healthy baseline
    if total_loans == 0:
        return 80, "OK"

    score = 0

    # i. Past Loans paid on time (40 Points)
    total_emis_paid = sum(l.emis_paid_on_time for l in loans)
    total_possible_emis = sum(l.tenure for l in loans)
    if total_possible_emis > 0:
        score += (total_emis_paid / total_possible_emis) * 40

    # ii. Number of loans taken in past (20 Points)
    if total_loans >= 3:
        score += 20
    elif total_loans >= 1:
        score += 10

    # iii. Loan activity in current year (20 Points)
    # High recent activity = Higher risk
    current_year_loans = loans.filter(start_date__year=date.today().year).count()
    if current_year_loans <= 1:
        score += 20
    elif current_year_loans <= 2:
        score += 10

    # iv. Loan volume vs Income (20 Points)
    annual_income = customer.monthly_salary * 12
    if total_loan_amount < (0.5 * annual_income):
        score += 20
    elif total_loan_amount < annual_income:
        score += 10

    return int(score), "OK"