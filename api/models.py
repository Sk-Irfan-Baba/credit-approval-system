from django.db import models

# Create your models here.
class Customer(models.Model):
    customer_id = models.IntegerField(primary_key=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone_number = models.BigIntegerField()
    monthly_salary = models.IntegerField()
    approved_limit= models.IntegerField()
    age = models.IntegerField()

class Loan(models.Model):
    customer_id = models.ForeignKey(Customer,on_delete=models.CASCADE)
    loan_id = models.IntegerField(primary_key=True)
    loan_amount = models.FloatField()
    tenure = models.IntegerField()
    interest_rate = models.FloatField()
    monthly_installment = models.IntegerField()
    emis_paid_on_time = models.IntegerField()
    start_date = models.DateField()
    end_date = models.DateField()
    