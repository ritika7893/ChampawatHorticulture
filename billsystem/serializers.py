from rest_framework import serializers
from .models import BillingItem, BillingReport,CenterComponentDetail,ComponentInvestment,Scheme,BeneficiaryRegistration,VikasKhandVidhanSabha,RegUser, RegUserActionLog,DemandGeneration,DemandByCenter,NurseryFinancial,NurseryPhysical,NurseryPhysicalRecipient
import json

from django.contrib.auth.hashers import make_password
class BillingItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = BillingItem
        fields = "__all__" 
        read_only_fields = ["center_id", "user_id"]
class LoginSerializer(serializers.Serializer):
    email_or_phone = serializers.CharField()
    password = serializers.CharField(write_only=True)

class BillingItemUpdateSerializer(serializers.Serializer):
    center_id = serializers.CharField()
    billing_date = serializers.DateField(required=False)
    bill_report_id = serializers.CharField()
    multiple_bills = serializers.ListField(
        child=serializers.ListField(
            child=serializers.CharField(),  # ["BILL-12345", "10"]
            min_length=2,
            max_length=2
        )
    )
class BillingItemMultiUserSerializer(serializers.Serializer):
    data = BillingItemUpdateSerializer(many=True)
class BillingReportSerializer(serializers.ModelSerializer):
    component_data = serializers.SerializerMethodField()

    class Meta:
        model = BillingReport
        fields = "__all__"

    def get_component_data(self, obj):
        normalized = []

        for comp in obj.component_data or []:

           
            if isinstance(comp, dict):
                normalized.append(comp)
                continue

          
            if isinstance(comp, list):
                normalized.append({
                    "bill_id": comp[0],
                    "sub_investment_name": comp[1],
                    "investment_name": comp[2],
                    "unit": comp[3],
                    "allocated_quantity": comp[4],
                    "rate": comp[5],
                    "updated_quantity": comp[6],
                    "buy_amount": comp[7],
                    "sold_amount": comp[8],
                    "source_of_receipt": comp[9],
                     "scheme_name": comp[10] if len(comp) > 10 else None,
                })

        return normalized
        
class CenterComponentDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = CenterComponentDetail
        fields = "__all__"
class ComponentInvestmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComponentInvestment
        fields = '__all__'

class SchemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scheme
        fields = '__all__'
        

class BeneficiaryRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = BeneficiaryRegistration
        fields = "__all__"
        
class CenterLookupSerializer(serializers.ModelSerializer):
    class Meta:
        model = VikasKhandVidhanSabha
        fields = ["vikas_khand_name", "vidhan_sabha_name"]


class RegUserPasswordUpdateSerializer(serializers.ModelSerializer):
    user_id = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)

    class Meta:
        model = RegUser
        fields = ["user_id", "password"]

    def validate_user_id(self, value):
        if not RegUser.objects.filter(user_id=value).exists():
            raise serializers.ValidationError("Invalid user_id")
        return value

    def update(self, instance, validated_data):
   
        user_id = validated_data.pop("user_id")

     
        old_data = json.dumps({"user_id": instance.user_id})

      
        instance.password = make_password(validated_data["password"])
        instance.save()

     
        request = self.context.get("request")
        ip_address = None
        if request:
            x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(",")[0].strip()
            else:
                ip_address = request.META.get("REMOTE_ADDR")

       
        RegUserActionLog.objects.create(
            user_id=user_id,
            action="PASSWORD_UPDATE",
            old_data=old_data,
            new_data=json.dumps({"password": "updated"}),
            ip_address=ip_address 
        )

        return instance
        
        

class DemandGenerationSerializer(serializers.ModelSerializer):
    amount = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = DemandGeneration
        fields = "__all__"
        read_only_fields = ["id", "created_at", "amount"]

    def get_amount(self, obj):
        if obj.allocated_quantity is not None and obj.rate is not None:
            return obj.allocated_quantity * obj.rate
        
class DemandByCenterSerializer(serializers.ModelSerializer):
    demand = DemandGenerationSerializer(source="demand_id", read_only=True)
    class Meta:
        model = DemandByCenter
        fields = "__all__"

class NurseryFinancialSerializer(serializers.ModelSerializer):
    class Meta:
        model = NurseryFinancial
        fields = "__all__"
        
        
        
class NurseryPhysicalSerializer(serializers.ModelSerializer):
    class Meta:
        model = NurseryPhysical
        fields = "__all__"


class NurseryPhysicalRecipientSerializer(serializers.ModelSerializer):
    nursery_details = NurseryPhysicalSerializer(
        source="nursery_physical",
        read_only=True
    )

    class Meta:
        model = NurseryPhysicalRecipient
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]
        
from rest_framework import serializers

class BillingReportItemUpdateSerializer(serializers.Serializer):
    bill_id = serializers.CharField()
    updated_quantity = serializers.DecimalField(
        max_digits=10,
        decimal_places=2
    )


class BillingReportUpdateSerializer(serializers.Serializer):
    old_bill_report_id = serializers.CharField()
    new_bill_report_id = serializers.CharField(required=False)
    billing_date = serializers.DateField(required=False)
    status = serializers.CharField(required=False)

    multiple_bills = BillingReportItemUpdateSerializer(
        many=True,
        required=False
    )