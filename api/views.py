from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Sum
from datetime import date, timedelta  # Added timedelta for date math
from .models import Customer, Loan
from .services.credit_score import calculate_credit_score

# --- Helper Function to avoid RawPostDataException ---
def perform_eligibility_check(customer_id, loan_amount, interest_rate, tenure):
    customer = get_object_or_404(Customer, customer_id=customer_id)
    score, message = calculate_credit_score(customer_id)

    approval = False
    corrected_rate = interest_rate

    # Eligibility Tiers based on Credit Score
    if score > 50:
        approval = True
    elif 50 >= score > 30:
        approval = True
        corrected_rate = max(12.0, interest_rate)
    elif 30 >= score > 10:
        approval = True
        corrected_rate = max(16.0, interest_rate)
    else:
        approval = False
        message = "Credit score too low"

    # Rule: Sum of all EMIs > 50% of monthly salary
    current_emis = Loan.objects.filter(customer_id=customer).aggregate(
        Sum('monthly_installment')
    )['monthly_installment__sum'] or 0
    
    # EMI calculation: A = P(1+r) / tenure
    new_emi = (loan_amount * (1 + (corrected_rate / 100))) / tenure
    
    if (current_emis + new_emi) > (0.5 * customer.monthly_salary):
        approval = False
        message = "Total EMIs exceed 50% of monthly income"

    return {
        "customer_id": customer_id,
        "approval": approval,
        "interest_rate": interest_rate,
        "corrected_interest_rate": corrected_rate,
        "tenure": tenure,
        "monthly_installment": round(new_emi, 2),
        "reason": message if not approval else "Approved"
    }

# --- API Endpoints ---

@api_view(['POST'])
def register_customer(request):
    data = request.data
    monthly_salary = data.get('monthly_salary')
    # Approved Limit logic: 36 * Monthly Salary rounded to nearest lakh
    approved_limit = round(36 * monthly_salary / 100000) * 100000

    customer = Customer.objects.create(
        first_name=data.get('first_name'),
        last_name=data.get('last_name'),
        age=data.get('age'),
        phone_number=data.get('phone_number'),
        monthly_salary=monthly_salary,
        approved_limit=approved_limit
    )

    return Response({
        "customer_id": customer.customer_id,
        "name": f"{customer.first_name} {customer.last_name}",
        "age": customer.age,
        "monthly_income": customer.monthly_salary,
        "approved_limit": customer.approved_limit,
        "phone_number": customer.phone_number
    }, status=201)

@api_view(['POST'])
def check_eligibility(request):
    data = request.data
    result = perform_eligibility_check(
        data.get('customer_id'),
        data.get('loan_amount'),
        data.get('interest_rate'),
        data.get('tenure')
    )
    return Response(result)

@api_view(['POST'])
def create_loan(request):
    data = request.data
    eligibility_resp = perform_eligibility_check(
        data.get('customer_id'),
        data.get('loan_amount'),
        data.get('interest_rate'),
        data.get('tenure')
    )
    
    if not eligibility_resp['approval']:
        return Response({
            "loan_id": None,
            "customer_id": eligibility_resp['customer_id'],
            "loan_approved": False,
            "message": eligibility_resp['reason'],
            "monthly_installment": 0
        })

    customer = Customer.objects.get(customer_id=eligibility_resp['customer_id'])
    
    # Date Calculation
    start_date = date.today()
    # Approximation: Tenure months * 30 days
    tenure_months = int(data.get('tenure'))
    end_date = start_date + timedelta(days=30 * tenure_months)
    
    loan = Loan.objects.create(
        customer_id=customer,
        loan_amount=data.get('loan_amount'),
        tenure=tenure_months,
        interest_rate=eligibility_resp['corrected_interest_rate'],
        monthly_installment=eligibility_resp['monthly_installment'],
        emis_paid_on_time=0,
        start_date=start_date,
        end_date=end_date  # Satisfies not-null constraint
    )

    return Response({
        "loan_id": loan.loan_id,
        "customer_id": customer.customer_id,
        "loan_approved": True,
        "monthly_installment": loan.monthly_installment
    }, status=201)

@api_view(['GET'])
def view_loan(request, loan_id):
    loan = get_object_or_404(Loan, loan_id=loan_id)
    cust = loan.customer_id
    return Response({
        "loan_id": loan.loan_id,
        "customer": {
            "id": cust.customer_id,
            "first_name": cust.first_name,
            "last_name": cust.last_name,
            "phone_number": cust.phone_number,
            "age": cust.age
        },
        "loan_amount": loan.loan_amount,
        "interest_rate": loan.interest_rate,
        "monthly_installment": loan.monthly_installment,
        "tenure": loan.tenure
    })

@api_view(['GET'])
def view_loans_by_customer(request, customer_id):
    loans = Loan.objects.filter(customer_id=customer_id)
    return Response([{
        "loan_id": l.loan_id,
        "loan_amount": l.loan_amount,
        "interest_rate": l.interest_rate,
        "monthly_installment": l.monthly_installment,
        "repayments_left": l.tenure - l.emis_paid_on_time
    } for l in loans])