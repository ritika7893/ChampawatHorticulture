import random
from django.db import models
import json
# Create your models here.
from decimal import Decimal
from django.core.serializers.json import DjangoJSONEncoder

class BillingItem(models.Model):
    bill_id = models.CharField(max_length=10, blank=True)

    center_id = models.CharField(max_length=20, blank=True)
    user_id = models.CharField(max_length=20, blank=True)

    center_name = models.CharField(max_length=255, blank=True, null=True)
   
    investment_name = models.CharField(max_length=255, blank=True, null=True)
    unit = models.CharField(max_length=100, blank=True, null=True)
    sub_investment_name = models.CharField(max_length=255, blank=True, null=True)
    allocated_quantity = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    rate = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    updated_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    amount_of_farmer_share = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    amount_of_subsidy = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    source_of_receipt = models.CharField(max_length=255, blank=True, null=True)
    scheme_name = models.CharField(max_length=255, default='')
    bill_date =models.DateField(null=True, blank=True)
    anudan_name = models.CharField(max_length=255, blank=True, null=True)
    remark=models.CharField(max_length=255, blank=True, null=True)
    vikas_khand_name = models.CharField(max_length=255,blank=True, null=True)
    vidhan_sabha_name = models.CharField(max_length=255,blank=True, null=True)
    farmer_selling_rate = models.DecimalField(max_digits=10,decimal_places=2,blank=True,null=True)
    farmer_subsidy_rate = models.DecimalField( max_digits=10,decimal_places=2,blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    def generate_unique_bill_id(self):
        """Generate a unique 5-digit bill number."""
        while True:
            random_number = str(random.randint(10000, 99999))   # 5-digit random number
            final_id = f"BILL-{random_number}"

            # Check if already exists
            if not BillingItem.objects.filter(bill_id=final_id).exists():
                return final_id


    def save(self, *args, **kwargs):
        if not self.bill_id:
            self.bill_id = self.generate_unique_bill_id()
        # ----- CENTER ID (same for same center_name) -----
        if not self.center_id:
            existing_center = BillingItem.objects.filter(
                center_name=self.center_name
            ).first()

            if existing_center:
                self.center_id = existing_center.center_id
            else:
                center_count = BillingItem.objects.values("center_name").distinct().count() + 1
                self.center_id = f"CENT-{center_count:03d}"

        # ----- USER ID (same for same source_of_receipt) -----
        if not self.user_id:
            existing_user = BillingItem.objects.filter(
                source_of_receipt=self.source_of_receipt
            ).first()

            if existing_user:
                self.user_id = existing_user.user_id
            else:
                user_count = BillingItem.objects.values("source_of_receipt").distinct().count() + 1
                self.user_id = f"USR-{user_count:03d}"

        super().save(*args, **kwargs)

    class Meta:
        db_table = "billing_2025_26"




    
class RegUser(models.Model):
    email = models.EmailField()
    password=models.CharField(max_length=300)
    username=models.CharField(max_length=300,null=True, blank=True)
    role=models.CharField(max_length=20,null=True, blank=True)
    user_id=models.CharField(max_length=20,null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now_add=True)
    
  

class BillingReport(models.Model):
    bill_report_id = models.CharField(max_length=15, blank=True)
    billing_date = models.DateField(null=True, blank=True)
    center_id = models.CharField(max_length=20, blank=True)
    component_data = models.JSONField(default=list, blank=True, null=True)
    center_name = models.CharField(max_length=255, blank=True, null=True)
    status=models.CharField(max_length=50,default='accepted')
    component_pageno = models.JSONField(default=list, blank=True, null=True)
    recipt_file=models.FileField(upload_to='receipts/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "billingreport_2025_26"
        
class CenterComponentDetail(models.Model):
    center_id = models.CharField(max_length=20, blank=True)
    user_id = models.CharField(max_length=20, blank=True)
    source_of_receipt = models.CharField(max_length=255)
    center_name = models.CharField(max_length=255, blank=True, null=True)
    component = models.CharField(max_length=255 ,blank=True, null=True)
    investment_name = models.CharField(max_length=255,blank=True, null=True)
    unit = models.CharField(max_length=100)
    scheme_name = models.CharField(max_length=255, default='')
    class Meta:
        db_table = "center_component_details"
        unique_together = ("center_id", "component", "investment_name")
        
class ComponentInvestment(models.Model):
    
    sub_investment_name = models.CharField(max_length=255, blank=True, null=True)
    investment_name = models.CharField(max_length=255, blank=True, null=True)
    unit = models.CharField(max_length=100)
    create_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.component} - {self.investment_name}"

    class Meta:
        db_table = "component_investments"
        unique_together = ( "investment_name", "sub_investment_name")

    
class Scheme(models.Model):
    scheme_name = models.CharField(max_length=255, unique=True)
    create_at = models.DateTimeField(auto_now_add=True)
    
    
class BeneficiaryRegistration(models.Model):
    beneficiary_id = models.CharField(max_length=20, unique=True, blank=True)  # Auto-generated
    farmer_name = models.CharField(max_length=255,blank=True, null=True)
    father_name = models.CharField(max_length=255,blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    vikas_khand_name = models.CharField(max_length=255,blank=True, null=True)
    vidhan_sabha_name = models.CharField(max_length=255,blank=True, null=True)
    center_name = models.CharField(max_length=255,blank=True, null=True)
    supplied_item_name = models.CharField(max_length=255,blank=True, null=True)
    unit = models.CharField(max_length=50,blank=True, null=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2,blank=True, null=True)
    rate = models.DecimalField(max_digits=10, decimal_places=2,blank=True, null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2,blank=True, null=True)
    aadhaar_number = models.CharField(max_length=20,blank=True, null=True)
    bank_account_number = models.CharField(max_length=30,blank=True, null=True)
    ifsc_code = models.CharField(max_length=20,blank=True, null=True)
    beneficiary_reg_date =models.DateField(null=True, blank=True)
    mobile_number = models.CharField(max_length=15,blank=True, null=True)
    category = models.CharField(max_length=100,blank=True, null=True)
    scheme_name = models.CharField(max_length=255,blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.beneficiary_id} - {self.farmer_name}"

    def generate_unique_beneficiary_id(self):
        last = BeneficiaryRegistration.objects.order_by('-id').first()
        if last and last.beneficiary_id:
            last_number = int(last.beneficiary_id.split('-')[-1])
            new_number = last_number + 1
        else:
            new_number = 1
        return f"BEN-{new_number:04d}"  # Example: BEN-0001

    def save(self, *args, **kwargs):
        if not self.beneficiary_id:
            self.beneficiary_id = self.generate_unique_beneficiary_id()
        super().save(*args, **kwargs)
        
        
class VikasKhandVidhanSabha(models.Model):
    vikas_khand_name = models.CharField(max_length=255)
    vidhan_sabha_name = models.CharField(max_length=255)
    center_name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.vikas_khand_name} - {self.vidhan_sabha_name} - {self.center_name}"
        
class BeneficiaryRegistrationLog(models.Model):
    beneficiary_id = models.CharField(max_length=20)
    action = models.CharField(max_length=10)  # UPDATE / DELETE
    old_data = models.TextField(null=True, blank=True)
    new_data = models.TextField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.beneficiary_id} - {self.action}"

class BillingItemLog(models.Model):
    ACTION_CHOICES = (
        ("UPDATE", "UPDATE"),
        ("DELETE", "DELETE"),
    )

    bill_id = models.CharField(max_length=20)
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    old_data = models.TextField(null=True, blank=True)
    new_data = models.TextField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "billing_item_log"

    def __str__(self):
        return f"{self.bill_id} - {self.action}"


class RegUserActionLog(models.Model):
    user_id = models.CharField(max_length=20)  
    action = models.CharField(max_length=80)   
    old_data = models.TextField(null=True, blank=True)
    new_data = models.TextField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user_id} - {self.action}"

 

class DemandGeneration(models.Model):
    demand_id = models.CharField(max_length=30, unique=True, editable=False)
    sub_investment_name = models.CharField(max_length=255, blank=True, null=True)
    unit=models.CharField(max_length=100, blank=True, null=True)
    allocated_quantity = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    rate = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    scheme_name = models.CharField(max_length=255,blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "demand_generation"

    def save(self, *args, **kwargs):
        if not self.demand_id:
            last_demand = DemandGeneration.objects.order_by('-id').first()
            if last_demand and last_demand.demand_id:
                last_number = int(last_demand.demand_id.split('-')[1])
                new_number = last_number + 1
            else:
                new_number = 1

            self.demand_id = f"DEM-{new_number:04d}"

        super().save(*args, **kwargs)
class DemandByCenter(models.Model):
    demand_id = models.ForeignKey(DemandGeneration, on_delete=models.CASCADE, related_name='demand_centers',to_field='demand_id',blank=True, null=True )
    center_name = models.CharField(max_length=255)
    demanded_quantity = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "demand_by_center"
        
class DemandGenerationLog(models.Model):
    ACTION_CHOICES = (
        ("UPDATE", "UPDATE"),
        ("DELETE", "DELETE"),
    )

    demand_id = models.CharField(max_length=30)
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    old_data = models.TextField(null=True, blank=True)
    new_data = models.TextField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "demand_generation_log"

    def __str__(self):
        return f"{self.demand_id} - {self.action}"
class DemandByCenterLog(models.Model):
    ACTION_CHOICES = (
        ("DELETE", "DELETE"),
        ("UPDATE", "UPDATE"),
    )

    demand_id = models.CharField(max_length=30)
    center_name = models.CharField(max_length=255)
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    old_data = models.TextField(null=True, blank=True)
    new_data = models.TextField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "demand_by_center_log"   


class NurseryFinancial(models.Model):
    nursery_name = models.CharField(max_length=255, blank=True, null=True)
    standard_item = models.CharField(max_length=100, blank=True, null=True)
    
    allocated_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    spent_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    registration_date =models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nursery_name} - {self.standard_item}"
    
class NurseryFinancialLog(models.Model):

    ACTION_CHOICES = (
        ("UPDATE", "UPDATE"),
        ("DELETE", "DELETE"),
    )

    nursery_financial_id = models.IntegerField()
    nursery_name = models.CharField(max_length=255, null=True, blank=True)
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)

    old_data = models.TextField(null=True, blank=True)
    new_data = models.TextField(null=True, blank=True)

    ip_address = models.GenericIPAddressField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    

    def __str__(self):
        return f"{self.nursery_financial_id} - {self.action}"
class NurseryPhysical(models.Model):
    
    nursery_name= models.CharField(max_length=255,blank=True, null=True)
    crop_name = models.CharField(max_length=255)
    unit = models.CharField(max_length=100)
    allocated_quantity = models.DecimalField(max_digits=12, decimal_places=2)
    allocated_amount = models.DecimalField(max_digits=12, decimal_places=2)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "production"

    def __str__(self):
        return f"{self.nursery_name} - {self.crop_name}"
    
class NurseryPhysicalRecipient(models.Model):
    nursery_physical = models.ForeignKey(NurseryPhysical, on_delete=models.CASCADE,related_name="recipients")
    recipient_name = models.CharField(max_length=255)
    recipient_quantity = models.DecimalField(max_digits=12, decimal_places=2)
    recipient_amount = models.DecimalField(max_digits=12, decimal_places=2)
    bill_number= models.CharField(max_length=20, blank=True, null=True)
    bill_date = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "production_recipient"

    def __str__(self):
        return f"{self.recipient_name} ({self.recipient_type})"
        
from .utils import beneficiary_model_to_dict, model_to_dict,demand_by_center_to_dict,demand_model_to_dict,nursery_financial_model_to_dict

from django.db.models.signals import pre_save, post_delete
from django.dispatch import receiver


@receiver(pre_save, sender=NurseryFinancial)
def nursery_financial_update_log(sender, instance, **kwargs):

    if not instance.pk:
        return

    try:
        old = NurseryFinancial.objects.get(pk=instance.pk)
    except NurseryFinancial.DoesNotExist:
        return

    old_data = {}
    new_data = {}

    for field in instance._meta.fields:
        name = field.name
    
        old_value = getattr(old, name)
        new_value = getattr(instance, name)
    
        # Skip auto fields
        if field.auto_created:
            continue
    
        # Convert Decimal safely
        if isinstance(old_value, Decimal):
            try:
                new_value = Decimal(new_value)
            except:
                pass
    
        if old_value != new_value:
            old_data[name] = old_value
            new_data[name] = new_value

    NurseryFinancialLog.objects.create(
        nursery_financial_id=old.id,
        nursery_name=old.nursery_name,
        action="UPDATE",
        ip_address=getattr(instance, "_ip_address", None),
        old_data=json.dumps(old_data, ensure_ascii=False, cls=DjangoJSONEncoder),
        new_data=json.dumps(new_data, ensure_ascii=False, cls=DjangoJSONEncoder),
    )
@receiver(post_delete, sender=NurseryFinancial)
def nursery_financial_delete_log(sender, instance, **kwargs):

    NurseryFinancialLog.objects.create(
        nursery_financial_id=instance.id,
        nursery_name=instance.nursery_name,
        action="DELETE",
        ip_address=getattr(instance, "_ip_address", None),
        old_data=json.dumps(
             nursery_financial_model_to_dict(instance),
            ensure_ascii=False,
            cls=DjangoJSONEncoder
        ),
        new_data=None,
    )

@receiver(pre_save, sender=BillingItem)
def billing_item_update_log(sender, instance, **kwargs):
    if not instance.pk:
        return

    try:
        old = BillingItem.objects.get(pk=instance.pk)
    except BillingItem.DoesNotExist:
        return

    old_data = {}
    new_data = {}

    for field in instance._meta.fields:
        name = field.name
        old_value = getattr(old, name)
        new_value = getattr(instance, name)

        if old_value != new_value:
            old_data[name] = old_value
            new_data[name] = new_value

    if not old_data:
        return
    
    BillingItemLog.objects.create(
        bill_id=old.bill_id,
        action="UPDATE",
        ip_address=getattr(instance, "_ip_address", None),
        old_data=json.dumps(old_data, ensure_ascii=False, cls=DjangoJSONEncoder),
        new_data=json.dumps(new_data, ensure_ascii=False, cls=DjangoJSONEncoder),
    )


@receiver(post_delete, sender=BillingItem)
def billing_item_delete_log(sender, instance, **kwargs):
   
    BillingItemLog.objects.create(
        bill_id=instance.bill_id,
        action="DELETE",
        ip_address=getattr(instance, "_ip_address", None),
        old_data=json.dumps(
            model_to_dict(instance),
            ensure_ascii=False,  cls=DjangoJSONEncoder
        ),
        new_data=None,
    )
@receiver(pre_save, sender=BeneficiaryRegistration)
def beneficiary_update_log(sender, instance, **kwargs):
    if not instance.pk:
        return

    try:
        old = BeneficiaryRegistration.objects.get(pk=instance.pk)
    except BeneficiaryRegistration.DoesNotExist:
        return

    old_data = {}
    new_data = {}

    for field in instance._meta.fields:
        name = field.name
        old_value = getattr(old, name)
        new_value = getattr(instance, name)

        if old_value != new_value:
            old_data[name] = old_value
            new_data[name] = new_value

    if not old_data:
        return

    BeneficiaryRegistrationLog.objects.create(
        beneficiary_id=old.beneficiary_id,
        action="UPDATE",
        old_data=json.dumps(old_data, ensure_ascii=False,cls=DjangoJSONEncoder),
        new_data=json.dumps(new_data, ensure_ascii=False,cls=DjangoJSONEncoder),
        ip_address=getattr(instance, "_ip_address", None)
    )

@receiver(post_delete, sender=BeneficiaryRegistration)
def beneficiary_delete_log(sender, instance, **kwargs):
    BeneficiaryRegistrationLog.objects.create(
        beneficiary_id=instance.beneficiary_id,
        action="DELETE",
        old_data=json.dumps(
            beneficiary_model_to_dict(instance),
            ensure_ascii=False
        ),
        new_data=None,
        ip_address=getattr(instance, "_ip_address", None)
    )
@receiver(pre_save, sender=DemandGeneration)
def demand_generation_update_log(sender, instance, **kwargs):
    if not instance.pk:
        return

    try:
        old = DemandGeneration.objects.get(pk=instance.pk)
    except DemandGeneration.DoesNotExist:
        return

    old_data = {}
    new_data = {}

    for field in instance._meta.fields:
        name = field.name
        old_value = getattr(old, name)
        new_value = getattr(instance, name)

        if old_value != new_value:
            old_data[name] = old_value
            new_data[name] = new_value

    if not old_data:
        return

    DemandGenerationLog.objects.create(
        demand_id=old.demand_id,
        action="UPDATE",
        ip_address=getattr(instance, "_ip_address", None),
        old_data=json.dumps(old_data, ensure_ascii=False, cls=DjangoJSONEncoder),
        new_data=json.dumps(new_data, ensure_ascii=False, cls=DjangoJSONEncoder),
    )
@receiver(post_delete, sender=DemandGeneration)
def demand_generation_delete_log(sender, instance, **kwargs):
    DemandGenerationLog.objects.create(
        demand_id=instance.demand_id,
        action="DELETE",
        ip_address=getattr(instance, "_ip_address", None),
        old_data=json.dumps(
            demand_model_to_dict(instance),
            ensure_ascii=False,
            cls=DjangoJSONEncoder
        ),
        new_data=None,
    )
@receiver(post_delete, sender=DemandByCenter)
def demand_by_center_delete_log(sender, instance, **kwargs):
    DemandByCenterLog.objects.create(
        demand_id=instance.demand_id_id,  
        center_name=instance.center_name,
        action="DELETE",  
        ip_address=getattr(instance, "_ip_address", None),
        old_data=json.dumps(
            demand_by_center_to_dict(instance),
            ensure_ascii=False,
            cls=DjangoJSONEncoder
        )
    )
@receiver(pre_save, sender=DemandByCenter)
def demand_by_center_update_log(sender, instance, **kwargs):
    if not instance.pk:
        return  # new record, not update

    try:
        old = DemandByCenter.objects.get(pk=instance.pk)
    except DemandByCenter.DoesNotExist:
        return

    old_data = {}
    new_data = {}

    for field in instance._meta.fields:
        name = field.name
        old_value = getattr(old, name)
        new_value = getattr(instance, name)

        if old_value != new_value:
            old_data[name] = old_value
            new_data[name] = new_value

    if not old_data:
        return  # nothing changed

    DemandByCenterLog.objects.create(
        demand_id=old.demand_id_id,
        center_name=old.center_name,
        action="UPDATE",
        ip_address=getattr(instance, "_ip_address", None),
        old_data=json.dumps(
            old_data,
            ensure_ascii=False,
            cls=DjangoJSONEncoder
        ),
        new_data=json.dumps(
            new_data,
            ensure_ascii=False,
            cls=DjangoJSONEncoder
        ),
    )


###OTHER PART################


from django.db import models


class UdyanCropStandard(models.Model):
    financial_year = models.CharField(max_length=20)
 
    crop_name = models.CharField(max_length=150)
 
    spacing = models.CharField(max_length=50)
 
    plants_per_hectare = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )
 
    plant_rate = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )
 
    pit_rate = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )
 
    manure_rate = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )
 
    manure_quantity = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )
 
    standard_total = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )
 
    standard_subsidy = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )
 
    is_active = models.BooleanField(default=True)
 
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
 
    class Meta:
        ordering = ["crop_name"]
        constraints = [
            models.UniqueConstraint(
                fields=["financial_year", "crop_name"],
                name="unique_udyan_crop_standard_year"
            )
        ]
 
    def __str__(self):
        return f"{self.crop_name} - {self.financial_year}"

class UdyanBill(models.Model):

    year = models.CharField(
        max_length=20,
        default="2026-27"
    )

    crop = models.ForeignKey(
        UdyanCropStandard,
        on_delete=models.PROTECT,
        related_name="bills"
    )

    area = models.DecimalField(
        max_digits=12,
        decimal_places=4
    )

    plants = models.PositiveIntegerField()

    calculation_basis = models.CharField(
        max_length=20,
        choices=[
            ("area", "Area"),
            ("plant", "Plant"),
        ],
        default="area"
    )

    rounding = models.PositiveSmallIntegerField(
        default=2
    )

    # Farmer details
    caste = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    heading = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    farmer_name = models.CharField(
        max_length=255
    )

    father_husband_name = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    date_of_birth = models.CharField(
        max_length=30,
        blank=True,
        null=True
    )

    village = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    center = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    bank_name_1 = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    account_number_1 = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    ifsc_1 = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    bank_name_2 = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    account_number_2 = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    ifsc_2 = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    aadhaar = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    mobile = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    pan = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    supplier_name = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    supplier_father_name = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    supplier_village = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    labour_name = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    labour_father_name = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    labour_village = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    # Calculated values
    plant_total = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0
    )

    pit_total = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0
    )

    manure_quantity = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0
    )

    manure_total = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0
    )

    plant_subsidy = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0
    )

    pit_subsidy = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0
    )

    manure_subsidy = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0
    )

    farmer_contribution = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0
    )

    grand_total = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0
    )

    grand_subsidy = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.farmer_name} - {self.crop.crop_name}"


class UdyanBillItem(models.Model):

    bill = models.ForeignKey(
        UdyanBill,
        on_delete=models.CASCADE,
        related_name="items"
    )

    item_number = models.PositiveSmallIntegerField()

    description = models.TextField()

    quantity = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0
    )

    rate = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0
    )

    total_expenditure = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0
    )

    subsidy = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0
    )

    farmer_contribution = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0
    )

    class Meta:
        ordering = ["item_number"]

    def __str__(self):
        return f"{self.bill_id} - Item {self.item_number}"
        
from decimal import Decimal

from django.db import models
from django.core.validators import MinValueValidator


class BeejMasterSetting(models.Model):
    financial_year = models.CharField(
        max_length=20,
        unique=True,
        default="2026-27"
    )

    purchase_limit = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=250000
    )

    project_cost = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=60000
    )

    max_subsidy = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=30000
    )

    farmer_share = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=30000
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ["financial_year"]

    def __str__(self):
        return self.financial_year


class BeejCentre(models.Model):
    name = models.CharField(
        max_length=150,
        unique=True
    )

    is_active = models.BooleanField(
        default=True
    )

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.name


class BeejVariety(models.Model):
    name = models.CharField(
        max_length=200,
        unique=True
    )

    jati = models.CharField(
        max_length=100,
        default="सा0जाति"
    )

    default_rate = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0
    )

    is_active = models.BooleanField(
        default=True
    )

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.name


class BeejStandard(models.Model):

    variety = models.ForeignKey(BeejVariety, on_delete=models.CASCADE, related_name="standards")
    item_label = models.CharField(max_length=255, default="खेत तैयारी + पौधशाला प्रबन्धन (कृषक अंश)")
    item_unit = models.CharField(max_length=100, default="हैक्टेयर-तुल्य")
    item_qty = models.DecimalField(max_digits=16, decimal_places=6, default=1)
    item_rate = models.DecimalField(max_digits=14, decimal_places=2, default=8700)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

   


    def __str__(self):
        return self.variety.name


class BeejPurchase(models.Model):

    date = models.DateField()

    variety = models.ForeignKey(
        BeejVariety,
        on_delete=models.PROTECT,
        related_name="purchases"
    )

    supplier = models.CharField(
        max_length=255,
        blank=True,
        default=""
    )

    qty_kg = models.DecimalField(
        max_digits=16,
        decimal_places=3,
        validators=[
            MinValueValidator(
                Decimal("0.001")
            )
        ]
    )

    rate = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[
            MinValueValidator(
                Decimal("0.01")
            )
        ]
    )

    amount = models.DecimalField(
        max_digits=16,
        decimal_places=2,
        default=0
    )

    ref = models.CharField(
        max_length=255,
        blank=True,
        default=""
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["date", "id"]

    def save(self, *args, **kwargs):
        self.amount = (
            self.qty_kg *
            self.rate
        )

        super().save(
            *args,
            **kwargs
        )


class BeejAllocation(models.Model):

    date = models.DateField()

    centre = models.ForeignKey(
        BeejCentre,
        on_delete=models.PROTECT,
        related_name="allocations"
    )

    variety = models.ForeignKey(
        BeejVariety,
        on_delete=models.PROTECT,
        related_name="allocations"
    )

    qty_gm = models.DecimalField(
        max_digits=16,
        decimal_places=3,
        validators=[
            MinValueValidator(
                Decimal("0.001")
            )
        ]
    )

    area = models.DecimalField(
        max_digits=16,
        decimal_places=6,
        default=0
    )

    project_cost = models.DecimalField(
        max_digits=16,
        decimal_places=2,
        default=0
    )

    subsidy = models.DecimalField(
        max_digits=16,
        decimal_places=2,
        default=0
    )

    farmer_share = models.DecimalField(
        max_digits=16,
        decimal_places=2,
        default=0
    )

    source = models.CharField(
        max_length=255,
        blank=True,
        default=""
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["date", "id"]


class BeejFarmerDistribution(models.Model):

    date = models.DateField()

    centre = models.ForeignKey(
        BeejCentre,
        on_delete=models.PROTECT,
        related_name="distributions"
    )

    variety = models.ForeignKey(
        BeejVariety,
        on_delete=models.PROTECT,
        related_name="distributions"
    )

    area = models.DecimalField(
        max_digits=16,
        decimal_places=6
    )

    name = models.CharField(
        max_length=255
    )

    father = models.CharField(
        max_length=255,
        blank=True,
        default=""
    )

    village = models.CharField(
        max_length=255,
        blank=True,
        default=""
    )

    mobile = models.CharField(
        max_length=30,
        blank=True,
        default=""
    )

    sign1 = models.CharField(
        max_length=20,
        default="नहीं"
    )

    sign2 = models.CharField(
        max_length=20,
        default="नहीं"
    )

    note = models.TextField(
        blank=True,
        default=""
    )

    seed_gm = models.DecimalField(
        max_digits=16,
        decimal_places=3,
        default=0
    )

    total = models.DecimalField(
        max_digits=16,
        decimal_places=2,
        default=0
    )

    subsidy = models.DecimalField(
        max_digits=16,
        decimal_places=2,
        default=0
    )

    farmer = models.DecimalField(
        max_digits=16,
        decimal_places=2,
        default=0
    )

    standard_snapshot = models.JSONField(
        default=dict,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["date", "id"]


class BeejFarmerDistributionItem(models.Model):

    distribution = models.ForeignKey(
        BeejFarmerDistribution,
        on_delete=models.CASCADE,
        related_name="items"
    )

    standard = models.ForeignKey(
        BeejStandard,
        on_delete=models.PROTECT,
        related_name="distribution_items"
    )

    label = models.CharField(
        max_length=255
    )

    unit = models.CharField(
        max_length=100,
        blank=True,
        default=""
    )

    qty = models.DecimalField(
        max_digits=16,
        decimal_places=6,
        default=0
    )

    rate = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0
    )

    amount = models.DecimalField(
        max_digits=16,
        decimal_places=2,
        default=0
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.label



class LibraryCategory(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class LibraryDocument(models.Model):
    category = models.ForeignKey(LibraryCategory, on_delete=models.CASCADE, related_name="documents")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to="library/documents/", blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
from django.db import models


class MonthReport(models.Model):
    month_report = models.FileField(upload_to="month_reports/", blank=True, null=True)
    month = models.PositiveIntegerField()
    financial_year = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.financial_year} - Month {self.month}"
        
        
        
from django.db import models, transaction


# ============================================================
# TABLE 1
# PERSONAL + LAND + IRRIGATION + GEOGRAPHICAL DETAILS
# ============================================================

class KisanPersonalLandDetails(models.Model):

    form_id = models.CharField(max_length=20,unique=True,editable=False)

    center_name = models.CharField(max_length=100, blank=True, null=True)
    form_id = models.CharField(max_length=20, unique=True, editable=False)
    plan_scheme = models.CharField(max_length=100, blank=True, null=True)
    fencing_type = models.CharField(max_length=100, blank=True, null=True)
    subsidy_ratio = models.CharField(max_length=100, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    gender = models.CharField(max_length=50, blank=True, null=True)
    father = models.CharField(max_length=255, blank=True, null=True)
    udyan_card = models.CharField(max_length=100, blank=True, null=True)
    village = models.CharField(max_length=255, blank=True, null=True)
    post = models.CharField(max_length=255, blank=True, null=True)
    block = models.CharField(max_length=255, blank=True, null=True)
    district = models.CharField(max_length=255, blank=True, null=True)
    mobile = models.CharField(max_length=15, blank=True, null=True)
    aadhaar = models.CharField(max_length=12, blank=True, null=True)
    category = models.CharField(max_length=100, blank=True, null=True)
    photo = models.ImageField(upload_to="kisan_applications/photos/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
   

   

   
    def save(self, *args, **kwargs):

        is_new = self.pk is None

        if is_new and not self.form_id:

            last_record = (
                KisanPersonalLandDetails.objects
                .filter(form_id__startswith="FORM-")
                .order_by("-id")
                .first()
            )

            if last_record:
                try:
                    last_number = int(
                        last_record.form_id.split("-")[1]
                    )
                except (ValueError, IndexError):
                    last_number = 0
            else:
                last_number = 0

            self.form_id = f"FORM-{last_number + 1:06d}"

        with transaction.atomic():

            super().save(*args, **kwargs)

            # Create blank records in Table 2 and Table 3
            # only when Table 1 is created for the first time.

            if is_new:

                KisanPlanTechnicalBankDetails.objects.get_or_create(
                    form_id=self.form_id
                )

                KisanApplicationDocuments.objects.get_or_create(
                    form_id=self.form_id
                )

    def __str__(self):
        return f"{self.form_id} - {self.name or ''}"

    class Meta:
        db_table = "kisan_personal_land_details"




class KisanPlanTechnicalBankDetails(models.Model):

    form_id = models.CharField(max_length=20, unique=True)
    total_land = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    proposed_area = models.DecimalField(max_digits=10, decimal_places=4, blank=True, null=True)
    latitude = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, blank=True, null=True)
    bank_name = models.CharField(max_length=255, blank=True, null=True)
    branch = models.CharField(max_length=255, blank=True, null=True)
    account = models.CharField(max_length=30, blank=True, null=True)
    ifsc = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.form_id

    class Meta:
        db_table = "kisan_plan_technical_bank_details"




class KisanApplicationDocuments(models.Model):

    form_id = models.CharField(max_length=20, unique=True)
    execution = models.CharField(max_length=150, blank=True, null=True)
    firm_name = models.CharField(max_length=255, blank=True, null=True)
    technical_standard_accepted = models.BooleanField(default=False)
    place = models.CharField(max_length=255, blank=True, null=True)
    application_date = models.DateField(blank=True, null=True)
    documents = models.JSONField(default=list, blank=True)
    declaration_accepted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.form_id

    class Meta:
        db_table = "kisan_application_documents"
        
class CenterLink(models.Model):
    center_names = models.JSONField(default=list, blank=True)
    link = models.URLField(max_length=500)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.link
        
class CenterLinkDetail(models.Model):
    center_link = models.ForeignKey(
        CenterLink,
        on_delete=models.CASCADE,
        related_name="details"
    )
    center_name = models.CharField(max_length=255)
    img = models.ImageField(upload_to="center_links/", blank=True, null=True)
    remark = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.center_name
        
class SalaryAttendanceReport(models.Model):
    center_name = models.CharField(max_length=255)
    month = models.CharField(max_length=20)
    financial_year = models.CharField(max_length=20)

  
    report_data = models.JSONField(default=dict)

  
    letter_number = models.CharField(max_length=100, blank=True, null=True)
    report_date = models.DateField(blank=True, null=True)
    subject = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-financial_year", "-id"]

    def __str__(self):
        return f"{self.center_name} - {self.month} - {self.financial_year}"
        
class MonthAttendanceReport(models.Model):
    month_attendance = models.FileField(upload_to="month_attendance/",blank=True,null=True)
    center_name = models.CharField(max_length=255)
    month = models.PositiveIntegerField()
    financial_year = models.CharField(max_length=20)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.center_name} - {self.financial_year} - Month {self.month}"