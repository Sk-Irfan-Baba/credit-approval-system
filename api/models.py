from django.db import models

class Customer(models.Model):
    # AutoField ensures the DB handles the ID incrementing after our sync
    customer_id = models.AutoField(primary_key=True) 
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    age = models.IntegerField()
    phone_number = models.CharField(max_length=20)
    monthly_salary = models.FloatField()
    approved_limit = models.FloatField()

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.customer_id})"

class Loan(models.Model):
    # Link to the Customer model
    customer_id = models.ForeignKey(Customer, on_delete=models.CASCADE)
    # AutoField for automatic ID generation
    loan_id = models.AutoField(primary_key=True)
    loan_amount = models.FloatField()
    tenure = models.IntegerField()
    interest_rate = models.FloatField()
    # FloatField handles the decimals (e.g., .33) correctly
    monthly_installment = models.FloatField() 
    emis_paid_on_time = models.IntegerField()
    start_date = models.DateField()
    # Nullable end_date prevents crashes during historical data import
    end_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Loan {self.loan_id} - {self.customer_id.first_name}"