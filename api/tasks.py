import pandas as pd
from celery import shared_task
from .models import Customer, Loan
import re
from django.db import connection

def clean_header(col):
    # Standardizes headers: "Monthly payment" -> "monthly_payment"
    s = str(col).strip().lower()
    s = re.sub(r'[^a-z0-9]', '_', s)
    return re.sub(r'_+', '_', s).strip('_')

@shared_task
def ingest_excel_data():
    # 1. Ingest Customer Data
    customer_df = pd.read_excel("customer_data.xlsx")
    customer_df.columns = [clean_header(c) for c in customer_df.columns]
    
    for _, row in customer_df.iterrows():
        Customer.objects.update_or_create(
            customer_id=int(row["customer_id"]),
            defaults={
                "first_name": row.get("first_name", ""),
                "last_name": row.get("last_name", ""),
                "age": int(row.get("age", 0)),
                "phone_number": str(row.get("phone_number", "")),
                "monthly_salary": float(row.get("monthly_salary", 0)),
                "approved_limit": float(row.get("approved_limit", 0)),
            }
        )

    # 2. Ingest Loan Data
    loan_df = pd.read_excel("loan_data.xlsx")
    loan_df.columns = [clean_header(c) for c in loan_df.columns]

    for _, row in loan_df.iterrows():
        try:
            customer = Customer.objects.get(customer_id=int(row["customer_id"]))
            Loan.objects.update_or_create(
                loan_id=int(row["loan_id"]),
                defaults={
                    "customer_id": customer,
                    "loan_amount": float(row["loan_amount"]),
                    "tenure": int(row["tenure"]),
                    "interest_rate": float(row["interest_rate"]),
                    "monthly_installment": float(row["monthly_payment"]), 
                    "emis_paid_on_time": int(row["emis_paid_on_time"]),
                    "start_date": row["date_of_approval"], 
                    "end_date": row["end_date"],
                }
            )
        except Customer.DoesNotExist:
            print(f"Skipping loan {row['loan_id']}: Customer {row['customer_id']} not found.")

    # --- ADDITION: AUTO-SYNC SEQUENCES ---
    # This ensures the DB 'counter' starts AFTER the highest ID we just imported
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT setval(pg_get_serial_sequence('api_customer', 'customer_id'), 
            (SELECT MAX(customer_id) FROM api_customer));
        """)
        cursor.execute("""
            SELECT setval(pg_get_serial_sequence('api_loan', 'loan_id'), 
            (SELECT MAX(loan_id) FROM api_loan));
        """)
            
    return "Data Ingestion and Sequence Reset Complete"