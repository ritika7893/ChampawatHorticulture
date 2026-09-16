from rest_framework import serializers
from .models import MonthAttendanceReport,SalaryAttendanceReport,BillingItem, BillingReport,CenterComponentDetail,ComponentInvestment,Scheme,BeneficiaryRegistration,VikasKhandVidhanSabha,RegUser, RegUserActionLog,DemandGeneration,DemandByCenter,NurseryFinancial,NurseryPhysical,NurseryPhysicalRecipient
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
    component_pageno = serializers.JSONField(required=False,allow_null=True)
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
    component_pageno = serializers.JSONField(required=False,allow_null=True)
    multiple_bills = BillingReportItemUpdateSerializer(
        many=True,
        required=False
    )
    
    
    
    
    
    
    
    
############OTHER PART#######################

from rest_framework import serializers

from .models import (
    UdyanCropStandard,
    UdyanBill,
    UdyanBillItem,
)


class UdyanCropStandardSerializer(serializers.ModelSerializer):
 
    class Meta:
        model = UdyanCropStandard
        fields = "__all__"
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]
 
    def validate(self, attrs):
        standard_total = attrs.get(
            "standard_total",
            getattr(self.instance, "standard_total", 0)
        )
 
        standard_subsidy = attrs.get(
            "standard_subsidy",
            getattr(self.instance, "standard_subsidy", 0)
        )
 
        if standard_total < 0:
            raise serializers.ValidationError({
                "standard_total": "Standard total cannot be negative."
            })
 
        if standard_subsidy < 0:
            raise serializers.ValidationError({
                "standard_subsidy": "Subsidy cannot be negative."
            })
 
        if standard_subsidy > standard_total:
            raise serializers.ValidationError({
                "standard_subsidy":
                    "Subsidy cannot be greater than standard total."
            })
 
        return attrs

class UdyanBillItemSerializer(
    serializers.ModelSerializer
):

    class Meta:
        model = UdyanBillItem
        fields = "__all__"


class UdyanBillSerializer(
    serializers.ModelSerializer
):

    crop_name = serializers.CharField(
        source="crop.crop_name",
        read_only=True
    )

    spacing = serializers.CharField(
        source="crop.spacing",
        read_only=True
    )

    items = UdyanBillItemSerializer(
        many=True,
        read_only=True
    )

    class Meta:
        model = UdyanBill

        fields = [
            "id",
            "year",
            "crop",
            "crop_name",
            "spacing",
            "area",
            "plants",
            "calculation_basis",
            "rounding",

            "caste",
            "heading",
            "farmer_name",
            "father_husband_name",
            "date_of_birth",
            "village",
            "center",

            "bank_name_1",
            "account_number_1",
            "ifsc_1",

            "bank_name_2",
            "account_number_2",
            "ifsc_2",

            "aadhaar",
            "mobile",
            "pan",

            "supplier_name",
            "supplier_father_name",
            "supplier_village",

            "labour_name",
            "labour_father_name",
            "labour_village",

            "plant_total",
            "pit_total",
            "manure_quantity",
            "manure_total",

            "plant_subsidy",
            "pit_subsidy",
            "manure_subsidy",

            "farmer_contribution",
            "grand_total",
            "grand_subsidy",

            "items",

            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "plant_total",
            "pit_total",
            "manure_quantity",
            "manure_total",
            "plant_subsidy",
            "pit_subsidy",
            "manure_subsidy",
            "farmer_contribution",
            "grand_total",
            "grand_subsidy",
            "created_at",
            "updated_at",
        ]
        
from decimal import Decimal

from django.db.models import Sum

from rest_framework import serializers

from .models import (
    BeejMasterSetting,
    BeejCentre,
    BeejVariety,
    BeejStandard,
    BeejPurchase,
    BeejAllocation,
    BeejFarmerDistribution,
)


class MasterSettingSerializer(
    serializers.ModelSerializer
):
    class Meta:
        model = BeejMasterSetting

        fields = [
            "id",
            "financial_year",
            "purchase_limit",
            "project_cost",
            "max_subsidy",
            "farmer_share",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "updated_at",
        ]


class CentreSerializer(
    serializers.ModelSerializer
):
    class Meta:
        model = BeejCentre

        fields = [
            "id",
            "name",
            "is_active",
        ]


class VarietySerializer(
    serializers.ModelSerializer
):
    class Meta:
        model = BeejVariety

        fields = [
            "id",
            "name",
            "jati",
            "default_rate",
            "is_active",
        ]


class StandardSerializer(serializers.ModelSerializer):
    variety_name = serializers.CharField(source="variety.name", read_only=True)
    variety_jati = serializers.CharField(source="variety.jati", read_only=True)

    class Meta:
        model = BeejStandard
        fields = ["id", "variety", "variety_name", "variety_jati", "item_label", "item_unit", "item_qty", "item_rate", "updated_at", "created_at"]

class PurchaseSerializer(
    serializers.ModelSerializer
):

    variety_name = serializers.CharField(
        source="variety.name",
        read_only=True
    )

    unit = serializers.SerializerMethodField()

    remaining_capacity = serializers.SerializerMethodField()

    class Meta:
        model = BeejPurchase

        fields = [
            "id",
            "date",
            "variety",
            "variety_name",
            "supplier",
            "qty_kg",
            "rate",
            "amount",
            "unit",
            "ref",
            "remaining_capacity",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "amount",
            "unit",
            "remaining_capacity",
            "created_at",
        ]

    def get_unit(
        self,
        obj
    ):
        return "kg"

    def get_remaining_capacity(
        self,
        obj
    ):
        master = (
            BeejMasterSetting.objects
            .filter(
                financial_year="2026-27"
            )
            .first()
        )

        if not master:
            return "0.00"

        total = (
            BeejPurchase.objects
            .filter(
                variety=obj.variety
            )
            .aggregate(
                total=Sum("amount")
            )["total"]
            or Decimal("0")
        )

        return str(
            max(
                Decimal("0"),
                master.purchase_limit - total
            )
        )

    def validate(self, attrs):
        qty = attrs.get(
            "qty_kg"
        )

        rate = attrs.get(
            "rate"
        )

        if (
            not qty
            or qty <= 0
            or not rate
            or rate <= 0
        ):
            raise serializers.ValidationError(
                "मात्रा और दर 0 से अधिक होनी चाहिए।"
            )

        return attrs

    def create(
        self,
        validated_data
    ):
        master = (
            BeejMasterSetting.objects
            .filter(
                financial_year="2026-27"
            )
            .first()
        )

        obj = BeejPurchase(
            **validated_data
        )

        current = (
            BeejPurchase.objects
            .filter(
                variety=obj.variety
            )
            .aggregate(
                total=Sum("amount")
            )["total"]
            or Decimal("0")
        )

        new_amount = (
            obj.qty_kg * obj.rate
        )

        if (
            master
            and current + new_amount >
            master.purchase_limit
        ):
            raise serializers.ValidationError(
                {
                    "qty_kg":
                        "इस किस्म की क्रय सीमा पार हो जाएगी।"
                }
            )

        obj.save()

        return obj

    def to_representation(
        self,
        instance
    ):
        data = super().to_representation(
            instance
        )

        data["qty_kg"] = str(
            instance.qty_kg
        )

        data["rate"] = str(
            instance.rate
        )

        data["amount"] = str(
            instance.amount
        )

        return data


class AllocationSerializer(
    serializers.ModelSerializer
):

    centre_name = serializers.CharField(
        source="centre.name",
        read_only=True
    )

    variety_name = serializers.CharField(
        source="variety.name",
        read_only=True
    )

    class Meta:
        model = BeejAllocation

        fields = [
            "id",
            "date",
            "centre",
            "centre_name",
            "variety",
            "variety_name",
            "qty_gm",
            "area",
            "project_cost",
            "subsidy",
            "farmer_share",
            "source",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "area",
            "project_cost",
            "subsidy",
            "farmer_share",
            "created_at",
        ]

    def validate(self, attrs):

        # Get master setting
        master = (
            BeejMasterSetting.objects
            .get(
                financial_year="2026-27"
            )
        )

        # Get latest standard for selected variety
        standard = (
            BeejStandard.objects
            .filter(
                variety=attrs["variety"]
            )
            .order_by("-updated_at", "-id")
            .first()
        )

        if not standard:
            raise serializers.ValidationError(
                {
                    "variety":
                    "इस किस्म के लिए बीज मानक उपलब्ध नहीं है।"
                }
            )

        qty = attrs["qty_gm"]

        # Validate standard
        if standard.item_qty <= 0:
            raise serializers.ValidationError(
                {
                    "variety":
                    "इस किस्म का बीज मानक मान्य नहीं है।"
                }
            )

        # Calculate area
        area = (
            qty /
            standard.item_qty
        )

        # Already allocated quantity
        allocated = (
            BeejAllocation.objects
            .filter(
                variety=attrs["variety"]
            )
            .aggregate(
                total=Sum("qty_gm")
            )["total"]
            or Decimal("0")
        )

        # Purchased quantity
        purchased = (
            BeejPurchase.objects
            .filter(
                variety=attrs["variety"]
            )
            .aggregate(
                total=Sum("qty_kg")
            )["total"]
            or Decimal("0")
        )

        purchased_gm = (
            purchased *
            Decimal("1000")
        )

        # Stock validation
        if allocated + qty > purchased_gm:

            available = (
                purchased_gm -
                allocated
            )

            raise serializers.ValidationError(
                {
                    "qty_gm":
                    f"केन्द्रीय स्टॉक कम है। उपलब्ध शेष {available} ग्राम है।"
                }
            )

        attrs["_area"] = area
        attrs["_master"] = master

        return attrs

    def create(
        self,
        validated_data
    ):

        area = validated_data.pop(
            "_area"
        )

        master = validated_data.pop(
            "_master"
        )

        obj = BeejAllocation(
            **validated_data,

            area=area,

            project_cost=(
                area *
                master.project_cost
            ),

            subsidy=(
                area *
                master.max_subsidy
            ),

            farmer_share=(
                area *
                master.farmer_share
            ),
        )

        obj.save()

        return obj

    def to_representation(
        self,
        instance
    ):

        data = super().to_representation(
            instance
        )

        for field in [
            "qty_gm",
            "area",
            "project_cost",
            "subsidy",
            "farmer_share",
        ]:

            data[field] = str(
                getattr(
                    instance,
                    field
                )
            )

        return data

from decimal import Decimal

from django.db import transaction
from django.db.models import Sum

from rest_framework import serializers

from .models import (
    BeejStandard,
    BeejAllocation,
    BeejFarmerDistribution,
    BeejFarmerDistributionItem,
)


class DistributionItemSerializer(
    serializers.ModelSerializer
):

    standard_label = serializers.CharField(
        source="standard.item_label",
        read_only=True
    )

    standard_unit = serializers.CharField(
        source="standard.item_unit",
        read_only=True
    )

    class Meta:
        model = BeejFarmerDistributionItem

        fields = [
            "id",
            "standard",
            "standard_label",
            "standard_unit",
            "label",
            "unit",
            "qty",
            "rate",
            "amount",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "standard_label",
            "standard_unit",
            "label",
            "unit",
            "qty",
            "rate",
            "amount",
            "created_at",
        ]


class DistributionSerializer(
    serializers.ModelSerializer
):

    centre_name = serializers.CharField(
        source="centre.name",
        read_only=True
    )

    variety_name = serializers.CharField(
        source="variety.name",
        read_only=True
    )

    items = DistributionItemSerializer(
        many=True,
        required=False
    )

    stock_after = serializers.SerializerMethodField()

    stock_warning = serializers.SerializerMethodField()

    class Meta:
        model = BeejFarmerDistribution

        fields = [
            "id",
            "date",
            "centre",
            "centre_name",
            "variety",
            "variety_name",
            "area",
            "name",
            "father",
            "village",
            "mobile",
            "sign1",
            "sign2",
            "note",
            "items",
            "seed_gm",
            "total",
            "subsidy",
            "farmer",
            "standard_snapshot",
            "stock_after",
            "stock_warning",
            "created_at",
        ]

        read_only_fields = [
            "id",
            "seed_gm",
            "total",
            "subsidy",
            "farmer",
            "standard_snapshot",
            "stock_after",
            "stock_warning",
            "created_at",
        ]

    def validate(self, attrs):

        variety = attrs.get("variety")
        area = attrs.get("area")

        if not area or area <= 0:
            raise serializers.ValidationError({
                "area": "क्षेत्रफल 0 से अधिक होना चाहिए।"
            })

        items = attrs.get("items", [])

        for item in items:

            standard = item.get("standard")

            if not standard:
                raise serializers.ValidationError({
                    "items": "Standard item required."
                })

            if standard.variety_id != variety.id:
                raise serializers.ValidationError({
                    "items":
                    f"Standard ID {standard.id} "
                    f"selected variety से संबंधित नहीं है।"
                })

        return attrs

    @transaction.atomic
    def create(self, validated_data):

        items_data = validated_data.pop(
            "items",
            []
        )

        area = validated_data["area"]

        distribution = (
            BeejFarmerDistribution.objects.create(
                **validated_data
            )
        )

        total = Decimal("0")

        snapshot = []

        for item_data in items_data:

            standard = item_data["standard"]

            qty = (
                area *
                standard.item_qty
            )

            amount = (
                qty *
                standard.item_rate
            )

            BeejFarmerDistributionItem.objects.create(
                distribution=distribution,
                standard=standard,
                label=standard.item_label,
                unit=standard.item_unit,
                qty=qty,
                rate=standard.item_rate,
                amount=amount,
            )

            total += amount

            snapshot.append({
                "standard_id": standard.id,
                "label": standard.item_label,
                "unit": standard.item_unit,
                "standard_qty": str(
                    standard.item_qty
                ),
                "rate": str(
                    standard.item_rate
                ),
                "qty": str(qty),
                "amount": str(amount),
            })

        distribution.total = total

        distribution.standard_snapshot = snapshot

        distribution.save(
            update_fields=[
                "total",
                "standard_snapshot",
            ]
        )

        return distribution

    @transaction.atomic
    def update(
        self,
        instance,
        validated_data
    ):

        items_data = validated_data.pop(
            "items",
            None
        )

        # Update normal distribution fields
        for attr, value in validated_data.items():

            setattr(
                instance,
                attr,
                value
            )

        instance.save()

        # Update items only when items are sent
        if items_data is not None:

            # Remove old items
            instance.items.all().delete()

            area = instance.area

            total = Decimal("0")

            snapshot = []

            for item_data in items_data:

                standard = item_data["standard"]

                qty = (
                    area *
                    standard.item_qty
                )

                amount = (
                    qty *
                    standard.item_rate
                )

                BeejFarmerDistributionItem.objects.create(
                    distribution=instance,
                    standard=standard,
                    label=standard.item_label,
                    unit=standard.item_unit,
                    qty=qty,
                    rate=standard.item_rate,
                    amount=amount,
                )

                total += amount

                snapshot.append({
                    "standard_id": standard.id,
                    "label": standard.item_label,
                    "unit": standard.item_unit,
                    "standard_qty": str(
                        standard.item_qty
                    ),
                    "rate": str(
                        standard.item_rate
                    ),
                    "qty": str(qty),
                    "amount": str(amount),
                })

            instance.total = total

            instance.standard_snapshot = snapshot

            instance.save(
                update_fields=[
                    "total",
                    "standard_snapshot",
                ]
            )

        return instance

    def get_stock_after(self, obj):

        received = (
            BeejAllocation.objects
            .filter(
                centre=obj.centre,
                variety=obj.variety
            )
            .aggregate(
                total=Sum("qty_gm")
            )["total"]
            or Decimal("0")
        )

        used = (
            BeejFarmerDistribution.objects
            .filter(
                centre=obj.centre,
                variety=obj.variety
            )
            .aggregate(
                total=Sum("seed_gm")
            )["total"]
            or Decimal("0")
        )

        return str(
            received - used
        )

    def get_stock_warning(self, obj):

        return (
            Decimal(
                self.get_stock_after(obj)
            ) < 0
        )

    def to_representation(self, instance):

        data = super().to_representation(
            instance
        )

        for field in [
            "area",
            "seed_gm",
            "total",
            "subsidy",
            "farmer",
        ]:

            data[field] = str(
                getattr(
                    instance,
                    field
                )
            )

        return data
        
  
from rest_framework import serializers
from .models import LibraryCategory, LibraryDocument      
class LibraryDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = LibraryDocument
        fields = ["id", "category", "title", "description", "file", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class LibraryCategorySerializer(serializers.ModelSerializer):
    documents = LibraryDocumentSerializer(many=True, read_only=True)
    document_count = serializers.SerializerMethodField()

    class Meta:
        model = LibraryCategory
        fields = ["id", "name", "description", "is_active", "document_count", "documents", "created_at", "updated_at"]
        read_only_fields = ["id", "document_count", "documents", "created_at", "updated_at"]

    def get_document_count(self, obj):
        return obj.documents.filter(is_active=True).count()
    
    
from .models import MonthReport    
class MonthReportSerializer(serializers.ModelSerializer):

    class Meta:
        model = MonthReport
        fields = ["id", "month_report", "month", "financial_year", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]
        extra_kwargs = {"month_report": {"required": False, "allow_null": True}}
        
        
from rest_framework import serializers

from .models import (
    KisanPersonalLandDetails,
    KisanPlanTechnicalBankDetails,
    KisanApplicationDocuments,
)


# ============================================================
# TABLE 1 SERIALIZER
# ============================================================

class KisanPersonalLandDetailsSerializer(serializers.ModelSerializer):

    class Meta:
        model = KisanPersonalLandDetails
        fields = [
            "form_id",

            # Personal
            "name",
            "gender",
            "father",
            "udyan_card",
            "village",
            "post",
            "block",
            "district",
            "mobile",
            "aadhaar",
            "category",

            # Land
            "total_land",
            "prop_area_val",
            "prop_area_unit",

            # Irrigation
            "irrigation",
            "irrigation_sources",
            "irrigation_other",

            # Geographical
            "altitude",
            "road_dist",
            "slope",
            "soil",
            "latitude",
            "longitude",

            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "form_id",
            "created_at",
            "updated_at",
        ]


# ============================================================
# TABLE 2 SERIALIZER
# ============================================================

class KisanPlanTechnicalBankDetailsSerializer(serializers.ModelSerializer):

    class Meta:
        model = KisanPlanTechnicalBankDetails

        fields = [
            "form_id",

            # Plan
            "plan_scheme",
            "cost_per_ha",
            "plan_type",
            "group_name",
            "contribution",
            "other_scheme",

            # Fencing
            "fencing_type",
            "subsidy_ratio",

            # Technical
            "execution",
            "firm_name",
            "technical_standard_accepted",

            # Bank
            "bank_name",
            "branch",
            "account",
            "ifsc",

            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "form_id",
            "created_at",
            "updated_at",
        ]


# ============================================================
# TABLE 3 SERIALIZER
# ============================================================

class KisanApplicationDocumentsSerializer(serializers.ModelSerializer):

    class Meta:
        model = KisanApplicationDocuments

        fields = [
            "form_id",

            # Application
            "place",
            "application_date",

            # Documents
            "documents",

            # Photo
            "photo",

            # Declaration
            "declaration_accepted",

            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "form_id",
            "created_at",
            "updated_at",
        ]


# ============================================================
# COMPLETE APPLICATION SERIALIZER
# ============================================================

class KisanCompleteApplicationSerializer(serializers.Serializer):

    personal = KisanPersonalLandDetailsSerializer()
    plan_technical_bank = KisanPlanTechnicalBankDetailsSerializer()
    application_documents = KisanApplicationDocumentsSerializer()

    def update(self, instance, validated_data):

        personal_data = validated_data.get(
            "personal",
            {}
        )

        plan_data = validated_data.get(
            "plan_technical_bank",
            {}
        )

        application_data = validated_data.get(
            "application_documents",
            {}
        )

        # ====================================================
        # TABLE 1
        # ====================================================

        for attr, value in personal_data.items():

            if attr not in [
                "form_id",
                "created_at",
                "updated_at"
            ]:
                setattr(
                    instance,
                    attr,
                    value
                )

        instance.save()

        # ====================================================
        # TABLE 2
        # ====================================================

        plan_instance = (
            KisanPlanTechnicalBankDetails.objects.get(
                form_id=instance.form_id
            )
        )

        for attr, value in plan_data.items():

            if attr not in [
                "form_id",
                "created_at",
                "updated_at"
            ]:
                setattr(
                    plan_instance,
                    attr,
                    value
                )

        plan_instance.save()

        # ====================================================
        # TABLE 3
        # ====================================================

        application_instance = (
            KisanApplicationDocuments.objects.get(
                form_id=instance.form_id
            )
        )

        for attr, value in application_data.items():

            if attr not in [
                "form_id",
                "created_at",
                "updated_at"
            ]:
                setattr(
                    application_instance,
                    attr,
                    value
                )

        application_instance.save()

        return instance
        
        
from rest_framework import serializers

from .models import (
    KisanPersonalLandDetails,
    KisanPlanTechnicalBankDetails,
    KisanApplicationDocuments,
)


class KisanPersonalLandDetailsSerializer(serializers.ModelSerializer):

    class Meta:
        model = KisanPersonalLandDetails

        fields = "__all__"

        read_only_fields = [
            "form_id",
            "created_at",
            "updated_at",
        ]


class KisanPlanTechnicalBankDetailsSerializer(serializers.ModelSerializer):

    class Meta:
        model = KisanPlanTechnicalBankDetails

        fields = "__all__"

        read_only_fields = [
            "form_id",
            "created_at",
            "updated_at",
        ]


class KisanApplicationDocumentsSerializer(serializers.ModelSerializer):

    class Meta:
        model = KisanApplicationDocuments

        fields = "__all__"

        read_only_fields = [
            "form_id",
            "created_at",
            "updated_at",
        ]
        
from .models import CenterLink,CenterLinkDetail


class CenterLinkSerializer(serializers.ModelSerializer):

    class Meta:
        model = CenterLink
        fields = "__all__"
        

class CenterLinkDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = CenterLinkDetail
        fields = "__all__"
        
class SalaryAttendanceReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalaryAttendanceReport
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]
        
class MonthAttendanceReportSerializer(serializers.ModelSerializer):

    class Meta:
        model = MonthAttendanceReport
        fields = "__all__"
        
        
from .models import (
    KiwiPersonalDetails,
    KiwiPlanLandBankDetails,
    KiwiApplicationDocuments,
)


class KiwiPersonalDetailsSerializer(serializers.ModelSerializer):

    class Meta:
        model = KiwiPersonalDetails
        fields = "__all__"

        read_only_fields = [
            "form_id",
            "created_at",
            "updated_at",
        ]


class KiwiPlanLandBankDetailsSerializer(serializers.ModelSerializer):

    class Meta:
        model = KiwiPlanLandBankDetails
        fields = "__all__"

        read_only_fields = [
            "form_id",
            "created_at",
            "updated_at",
        ]


class KiwiApplicationDocumentsSerializer(serializers.ModelSerializer):

    class Meta:
        model = KiwiApplicationDocuments
        fields = "__all__"

        read_only_fields = [
            "form_id",
            "created_at",
            "updated_at",
        ]
        
from rest_framework import serializers

from .models import (
    DragonPersonalDetails,
    DragonPlanLandBankDetails,
    DragonApplicationDocuments,
)


class DragonPersonalDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = DragonPersonalDetails
        fields = "__all__"
        read_only_fields = [
            "form_id",
            "created_at",
            "updated_at",
        ]



class DragonPlanLandBankDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = DragonPlanLandBankDetails
        fields = "__all__"
        read_only_fields = [
            "form_id",
            "created_at",
            "updated_at",
        ]



class DragonApplicationDocumentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = DragonApplicationDocuments
        fields = "__all__"
        read_only_fields = [
            "form_id",
            "created_at",
            "updated_at",
        ]
