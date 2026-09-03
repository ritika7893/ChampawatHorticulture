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
    vikas_khand_name = models.CharField(max_length=255,blank=True, null=True)
    vidhan_sabha_name = models.CharField(max_length=255,blank=True, null=True)
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
   
    center_name = models.CharField(max_length=255, blank=True, null=True)
    status=models.CharField(max_length=50,default='accepted')
    component_data = models.JSONField(default=list, blank=True, null=True)
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

