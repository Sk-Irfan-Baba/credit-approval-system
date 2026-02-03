from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Customer, Loan
from .serializers import RegisterCustomerSerializer, LoanSerializer
from api.services.credit_score import calculate_credit_score
from django.db.models import Sum

@api_view(["POST"])
def register_customer(request):
    data = request.data
    # 36x monthly salary rounded to nearest lakh
    approved_limit = round((36 * data["monthly_income"]) / 100000) * 100000

    customer = Customer.objects.create(
        first_name=data["first_name"],
        last_name=data["last_name"],
        age=data["age"],
        phone_number=data["phone_number"],
        monthly_salary=data["monthly_income"],
        approved_limit=approved_limit,
    )

    serializer = RegisterCustomerSerializer(customer)
    return Response(serializer.data, status=status.HTTP_201_CREATED)

@api_view(["POST"])
def check_eligibility(request):
    customer_id = request.data.get("customer_id")
    loan_amount = request.data.get("loan_amount")
    interest_rate = request.data.get("interest_rate")
    tenure = request.data.get("tenure")

    customer = get_object_or_404(Customer, customer_id=customer_id)
    score, reason = calculate_credit_score(customer_id)

    # 1. Determine Tiered Interest Rate
    approval = False
    corrected_interest_rate = interest_rate

    if score > 50:
        approval = True
    elif 30 < score <= 50:
        approval = True
        corrected_interest_rate = max(interest_rate, 12.0)
    elif 10 < score <= 30:
        approval = True
        corrected_interest_rate = max(interest_rate, 16.0)
    else:
        approval = False
        reason = "Credit score too low"

    # 2. Calculate EMI using Compound Interest: A = P(1 + r)^t
    # r is annual rate, t is time in years
    r = corrected_interest_rate / 100
    t = tenure / 12
    total_repayment = loan_amount * ((1 + r) ** t)
    monthly_installment = total_repayment / tenure

    # 3. Final Hard Rule: Sum of ALL EMIs (Existing + New) < 50% Salary
    existing_emis = Loan.objects.filter(customer_id=customer).aggregate(Sum('monthly_installment'))['monthly_installment__sum'] or 0
    if (existing_emis + monthly_installment) > (0.5 * customer.monthly_salary):
        approval = False
        reason = "Total EMIs exceed 50% of monthly income"

    return Response({
        "customer_id": customer_id,
        "approval": approval,
        "interest_rate": interest_rate,
        "corrected_interest_rate": corrected_interest_rate,
        "tenure": tenure,
        "monthly_installment": round(monthly_installment, 2),
        "reason": reason if not approval else "Eligible"
    })

@api_view(["POST"])
def create_loan(request):
    # This endpoint re-runs eligibility to ensure data hasn't changed
    eligibility_response = check_eligibility(request).data
    
    if not eligibility_response["approval"]:
        return Response({
            "loan_id": None,
            "customer_id": request.data.get("customer_id"),
            "loan_approved": False,
            "message": eligibility_response.get("reason", "Loan not approved"),
            "monthly_installment": 0
        }, status=status.HTTP_200_OK)

    # Create the loan record
    customer = Customer.objects.get(customer_id=request.data.get("customer_id"))
    new_loan = Loan.objects.create(
        customer_id=customer,
        loan_amount=request.data.get("loan_amount"),
        interest_rate=eligibility_response["corrected_interest_rate"],
        tenure=request.data.get("tenure"),
        monthly_installment=eligibility_response["monthly_installment"],
        emis_paid_on_time=0
    )

    return Response({
        "loan_id": new_loan.loan_id,
        "customer_id": customer.customer_id,
        "loan_approved": True,
        "message": "Loan approved and created",
        "monthly_installment": new_loan.monthly_installment
    }, status=status.HTTP_201_CREATED)

@api_view(["GET"])
def view_loan(request, loan_id):
    loan = get_object_or_404(Loan, loan_id=loan_id)
    customer = loan.customer_id
    
    return Response({
        "loan_id": loan.loan_id,
        "customer": {
            "id": customer.customer_id,
            "first_name": customer.first_name,
            "last_name": customer.last_name,
            "phone_number": customer.phone_number,
            "age": customer.age
        },
        "loan_amount": loan.loan_amount,
        "interest_rate": loan.interest_rate,
        "monthly_installment": loan.monthly_installment,
        "tenure": loan.tenure
    })

@api_view(["GET"])
def view_loans_by_customer(request, customer_id):
    loans = Loan.objects.filter(customer_id=customer_id)
    response_data = []
    for loan in loans:
        response_data.append({
            "loan_id": loan.loan_id,
            "loan_amount": loan.loan_amount,
            "interest_rate": loan.interest_rate,
            "monthly_installment": loan.monthly_installment,
            "repayments_left": loan.tenure - loan.emis_paid_on_time
        })
    return Response(response_data)