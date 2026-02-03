from datetime import date
from django.db.models import Sum
from api.models import Loan, Customer

def calculate_credit_score(customer_id: int):
    try:
        customer = Customer.objects.get(customer_id=customer_id)
    except Customer.DoesNotExist:
        return 0, "Customer not found"

    loans = Loan.objects.filter(customer_id=customer)
    total_loans = loans.count()

    # ---- HARD REJECTION RULES ----
    
    # 1. Total debt vs Approved Limit
    # Note: If they have already reached their limit, score is 0.
    total_loan_amount = loans.aggregate(total=Sum("loan_amount"))["total"] or 0
    if total_loan_amount > customer.approved_limit:
        return 0, "Current debt exceeds approved limit"

    # 2. Total EMI vs 50% of monthly salary
    total_emi = loans.aggregate(total=Sum("monthly_installment"))["total"] or 0
    if total_emi > (0.5 * customer.monthly_salary):
        return 0, "Total EMIs exceed 50% of monthly salary"

    # ---- SCORING (Scale of 100) ----
    
    # Handle New Customers (No loan history)
    if total_loans == 0:
        # Assign a neutral-to-high baseline score so they aren't auto-rejected
        return 80, "New customer - no debt history"

    score = 0

    # Component 1: Past Loans paid on time (30 Points)
    # Fixed: Ratio of total EMIs paid on time to the total tenure of all loans
    total_tenure = sum(loan.tenure for loan in loans)
    total_on_time = sum(loan.emis_paid_on_time for loan in loans)
    
    if total_tenure > 0:
        on_time_ratio = total_on_time / total_tenure
        score += (on_time_ratio * 30)

    # Component 2: Number of loans taken in past (20 Points)
    # Having some history is better than having too much debt
    if total_loans <= 3:
        score += 20
    elif total_loans <= 6:
        score += 10
    else:
        score += 5

    # Component 3: Loan activity in current year (20 Points)
    current_year = date.today().year
    loans_this_year = loans.filter(start_date__year=current_year).count()
    if loans_this_year <= 1:
        score += 20
    elif loans_this_year <= 3:
        score += 10
    else:
        score += 0 # High recent activity reduces score

    # Component 4: Loan volume vs Income (30 Points)
    # Is the total loan amount sustainable compared to annual income?
    annual_income = customer.monthly_salary * 12
    if total_loan_amount <= (0.3 * annual_income):
        score += 30
    elif total_loan_amount <= (0.6 * annual_income):
        score += 15
    else:
        score += 5

    return int(score), "OK"