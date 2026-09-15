from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import JsonResponse
from .models import BillingItem, BillingReport, RegUser,CenterComponentDetail,Scheme,ComponentInvestment,BeneficiaryRegistration,VikasKhandVidhanSabha,DemandGeneration,DemandByCenter,NurseryFinancial,NurseryPhysicalRecipient,NurseryPhysical
from .serializers import BillingReportUpdateSerializer,BillingItemSerializer, BillingItemUpdateSerializer, BillingReportSerializer,CenterComponentDetailSerializer,NurseryFinancialSerializer,SchemeSerializer,RegUserPasswordUpdateSerializer,NurseryPhysicalSerializer, NurseryPhysicalRecipientSerializer,DemandGenerationSerializer,DemandByCenterSerializer,CenterLookupSerializer,BeneficiaryRegistrationSerializer,ComponentInvestmentSerializer,BillingItemMultiUserSerializer
from django.contrib.auth.hashers import check_password
import pandas as pd
import requests
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
import os
import zipfile
import tempfile
from django.http import FileResponse
from rest_framework.decorators import api_view
from django.shortcuts import get_object_or_404
from django.db import transaction
from .utils import generate_billing_report_pdf, get_client_ip, normalize_json
from django.db.models import Q
from rest_framework import status
from decimal import Decimal
from django.core.files.storage import default_storage
class BillingItemList(APIView):
    def get(self, request):
        bill_id = request.query_params.get("bill_id")

        queryset = BillingItem.objects.all()

        if bill_id:
            queryset = queryset.filter(bill_id=bill_id)

        queryset = queryset.order_by("-created_at")
        serializer = BillingItemSerializer(queryset, many=True)
        return Response(serializer.data)
    def post(self, request):
        data = request.data.copy()

       
        investment_name = data.get("investment_name")
        sub_investment_name = data.get("sub_investment_name")  # Added
        unit = data.get("unit")
        scheme_name = data.get("scheme_name")
        center_name = data.get("center_name")

        # Handle Scheme creation
        if scheme_name:
            Scheme.objects.get_or_create(
                scheme_name=scheme_name.strip()
            )
        if center_name and not data.get("vikas_khand_name") and not data.get("vidhan_sabha_name"):
            try:
                mapping = VikasKhandVidhanSabha.objects.get(
                    center_name=center_name
                )
                data["vikas_khand_name"] = mapping.vikas_khand_name
                data["vidhan_sabha_name"] = mapping.vidhan_sabha_name
            except VikasKhandVidhanSabha.DoesNotExist:
                data["vikas_khand_name"] = None
                data["vidhan_sabha_name"] = None

        # Handle ComponentInvestment creation
       
        ComponentInvestment.objects.get_or_create(
               
                investment_name=investment_name.strip() if investment_name else None,
                sub_investment_name=sub_investment_name.strip() if sub_investment_name else None,
                defaults={"unit": unit}
            )

        serializer = BillingItemSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Billing item created successfully"},
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    def put(self, request):
        item_id = request.data.get("bill_id")

        if not item_id:
            return Response(
                {"error": "id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            item = BillingItem.objects.get(bill_id=item_id)
        except BillingItem.DoesNotExist:
            return Response(
                {"error": "Billing item not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # ❗ Remove 'id' so it won't be updated
        data = request.data.copy()
        data.pop("bill_id", None)
        
        item._ip_address = get_client_ip(request)
        # Update ALL model fields dynamically
        for field in item._meta.fields:
            field_name = field.name

            if field_name in data:
                setattr(item, field_name, data.get(field_name))

        item.save() 

        return Response(
            {"message": "Billing item updated successfully"},
            status=status.HTTP_200_OK
        )
    def delete(self, request):
        bill_ids = request.data.get("bill_id")
    
        if not bill_ids:
            return Response(
                {"success": False, "message": "bill_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
        # ✅ Convert single → list
        if isinstance(bill_ids, (str, int)):
            bill_ids = [bill_ids]
    
        if not isinstance(bill_ids, list):
            return Response(
                {"success": False, "message": "bill_id must be string/int or list"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
        ip_address = get_client_ip(request)
    
        deleted_ids = []
        not_found_ids = []
    
        for b_id in bill_ids:
            try:
                item = BillingItem.objects.get(bill_id=b_id)
    
                # ✅ attach IP for logging
                item._ip_address = ip_address
    
                item.delete()
                deleted_ids.append(b_id)
    
            except BillingItem.DoesNotExist:
                not_found_ids.append(b_id)
    
        return Response(
            {
                "success": True,
               
                "message": f"{len(deleted_ids)} billing item(s) deleted successfully"
            },
            status=status.HTTP_200_OK
        )
class LoginAPIView(APIView):
    def post(self, request):
        username = request.data.get("username", "").lower()
        email = request.data.get("email","").lower()
        password = request.data.get("password")

        if not password or (not username and not email):
            return Response(
                {"error": "username or email and password are required"},
                status=400
            )
        
        # Login using username OR email
        user = RegUser.objects.filter(
            Q(username=username) | Q(email=email)
        ).first()

        if not user:
            return Response({"error": "User not found"}, status=404)
        if not check_password(password, user.password):
            return Response({"error": "Invalid password"}, status=400)

        return Response({
            "message": "Login success",
           
            "user_id": user.user_id,
            "role": user.role
        })
class BillingItemBulkUpload(APIView):
    def post(self, request):
        file = request.FILES.get("file")

        if not file:
            return Response({"error": "No file uploaded"}, status=400)

        try:
            if file.name.endswith(".csv"):
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file)
        except Exception as e:
            return Response({"error": str(e)}, status=400)

        # Normalize headers
        df.columns = (
            df.columns
            .str.strip()
            .str.lower()
            .str.replace(" ", "_")
        )

        # Convert NaN → None
        df = df.where(pd.notnull(df), None)

        required_cols = [
            "center_name",
            "component",
            "investment_name",
            "sub_investment_name",
            "unit",
            "allocated_quantity",
            "rate",
            "source_of_receipt",
            "scheme_name",
            "vikas_khand_name",
            "vidhan_sabha_name"
        ]

        missing_cols = [c for c in required_cols if c not in df.columns]
        if missing_cols:
            return Response(
                {"error": f"Missing columns: {', '.join(missing_cols)}"},
                status=400
            )

        created_count = 0
        errors = []

        for index, row in df.iterrows():
            data = row.to_dict()

         
            scheme_name = data.get("scheme_name")
            if scheme_name:
                Scheme.objects.get_or_create(scheme_name=scheme_name.strip())

            component = data.get("component")
            investment_name = data.get("investment_name")
            sub_investment_name = data.get("sub_investment_name")
            unit = data.get("unit")

            
            ComponentInvestment.objects.get_or_create(
                    component=component.strip() if component else None,
                    investment_name=investment_name.strip() if investment_name else None,
                    sub_investment_name=sub_investment_name.strip() if sub_investment_name else None,
                    defaults={"unit": unit}
                )

           
            serializer = BillingItemSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                created_count += 1
            else:
                errors.append({
                    "row": index + 2,  # Excel/CSV row number
                    "errors": serializer.errors
                })

        if errors:
            return Response(
                {"message": "Some rows failed", "errors": errors},
                status=400
            )

        return Response(
            {"message": f"{created_count} billing items uploaded successfully"},
            status=201
        )

class UpdateBillingItemQuantity(APIView):

   

    def post(self, request):
        serializer = BillingItemMultiUserSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        reports = []
        errors = []

        ip_address = request.META.get('HTTP_X_FORWARDED_FOR')
        if ip_address:
            ip_address = ip_address.split(',')[0].strip()
        else:
            ip_address = request.META.get('REMOTE_ADDR')

        for center_block in serializer.validated_data["data"]:
            center_id = center_block["center_id"]
            multiple_bills = center_block["multiple_bills"]
            billing_date = center_block.get("billing_date")
            bill_report_id = center_block.get("bill_report_id")
            component_pageno = center_block.get("component_pageno")
            center_items = BillingItem.objects.filter(center_id=center_id)

            if BillingReport.objects.filter(
                bill_report_id=bill_report_id
            ).exists():
                errors.append({
                    "bill_report_id": bill_report_id,
                    "error": "Bill Report ID already exists."
                })
                continue

            component_list = []
            first_item = None

            try:
                with transaction.atomic():

                    for bill_entry in multiple_bills:
                        bill_id, updated_quantity = bill_entry

                        item = center_items.filter(
                            bill_id=bill_id
                        ).first()

                        if not item:
                            continue

                        if first_item is None:
                            first_item = item

                        setattr(item, "_ip_address", ip_address)

                        item.updated_quantity = updated_quantity

                        # ==========================================
                        # BILL RATE ACCORDING TO SCHEME
                        # ==========================================

                        scheme_name = (item.scheme_name or "").strip()

                        selling_rate_schemes = [
                            "4401 बिक्री हेतु",
                            "मुख्यमंत्री एकीकृत विकास योजना"
                        ]

                        if scheme_name in selling_rate_schemes:
                            bill_rate = item.farmer_selling_rate or 0
                        else:
                            bill_rate = item.farmer_subsidy_rate or 0

                        # Save selected billing rate
                        item.rate = bill_rate

                        item.save()

                        allocated_qty = item.allocated_quantity or 0
                        updated_qty = item.updated_quantity or 0
                        rate = item.rate or 0

                        # ==========================================
                        # AMOUNT CALCULATION
                        # ==========================================

                        buy_amount = float(allocated_qty) * float(rate)
                        sold_amount = float(updated_qty) * float(rate)

                        component_list.append([
                            str(item.bill_id),

                            str(item.sub_investment_name),
                            str(item.investment_name),
                            str(item.unit),

                            str(allocated_qty),
                            str(rate),
                            str(updated_qty),

                            str(buy_amount),
                            str(sold_amount),

                            str(item.source_of_receipt),
                            str(item.scheme_name),
                        ])

                    if not component_list:
                        errors.append({
                            "center_id": center_id,
                            "error": "No bill IDs matched"
                        })
                        continue

                    report = BillingReport.objects.create(
                        billing_date=billing_date,
                        bill_report_id=bill_report_id,
                        center_id=first_item.center_id,
                        center_name=first_item.center_name,
                        component_data=component_list,
                        component_pageno=component_pageno
                    )

                    pdf_url = generate_billing_report_pdf(report)

                    reports.append(normalize_json({
                        "center_id": center_id,
                        "bill_report_id": str(report.bill_report_id),
                        "billing_date": (
                            report.billing_date.isoformat()
                            if report.billing_date else None
                        ),
                        "pdf_file": pdf_url,
                        "ip_address": ip_address
                    }))

            except Exception as e:
                import traceback

                errors.append({
                    "center_id": center_id,
                    "error": str(e),
                    "trace": traceback.format_exc()
                })

        if errors:
            return Response(
                {
                    "reports": reports,
                    "errors": errors
                },
                status=400
            )

        return Response(
            {
                "report_created": True,
                "reports": reports
            },
            status=200
        )


    def put(self, request):
        bill_report_id = request.data.get("bill_report_id")
        new_status = request.data.get("status")

        if not bill_report_id:
            return Response({"error": "bill_report_id is required"}, status=400)

        if not new_status:
            return Response({"error": "status is required"}, status=400)

        try:
            report = BillingReport.objects.get(bill_report_id=bill_report_id)
        except BillingReport.DoesNotExist:
            return Response({"error": "Bill Report ID not found"}, status=404)

        
        if new_status.lower() == "cancelled":
            for component in report.component_data:
                # component is a LIST
                bill_id = component[0]              
                report_updated_qty = float(component[6]) 

                item = BillingItem.objects.filter(
                    bill_id=bill_id,
                    center_id=report.center_id
                ).first()

                if item:
                    current_updated_qty = float(item.updated_quantity or 0)

                    # subtract report quantity
                    new_qty = current_updated_qty - report_updated_qty

                    # safety: no negative values
                    item.updated_quantity = max(new_qty, 0)
                    item.save(update_fields=["updated_quantity"])

            # regenerate PDF with CANCELLED watermark
            generate_billing_report_pdf(report, cancelled=True)

        # update report status
        report.status = new_status
        report.save(update_fields=["status"])
        report.delete()

        return Response(
            {"message": "Status updated successfully"},
            status=200
        )
        
class BillingReportList(APIView):

    
    def get(self, request):
        user_id = request.query_params.get("user_id")
        center_id = request.query_params.get("center_id")
        month = request.query_params.get("month")
        year = request.query_params.get("year")

        queryset = BillingReport.objects.all().order_by("-created_at")

       
        if user_id:
            queryset = queryset.filter(user_id=user_id)

        # ðŸ”¹ Filter by center_id
        if center_id:
            queryset = queryset.filter(center_id=center_id)

        # ðŸ”¹ Filter by month & year from created_at
        if month and year:
            queryset = queryset.filter(
                created_at__month=int(month),
                created_at__year=int(year)
            )

        serializer = BillingReportSerializer(queryset, many=True)
        return Response(serializer.data)
class CenterComponentDetailListAPIView(APIView):
   

    def post(self, request):
        data = request.data

        component = data.get("component")
        investment_name = data.get("investment_name")
        unit = data.get("unit")
        scheme_name = data.get("scheme_name", "")
        center_name = data.get("center_name")
        source_of_receipt = data.get("source_of_receipt")

        if not component or not investment_name:
            return Response({"error": "component and investment_name are required"},
                            status=status.HTTP_400_BAD_REQUEST)

        # Generate center_id
        if center_name:
            existing_center = CenterComponentDetail.objects.filter(center_name=center_name).first()
            if existing_center:
                center_id = existing_center.center_id
            else:
                center_count = CenterComponentDetail.objects.values("center_name").distinct().count() + 1
                center_id = f"CENT-{center_count:03d}"
        else:
            center_id = "CENT-000"

        # Generate user_id
        if source_of_receipt:
            existing_user = CenterComponentDetail.objects.filter(source_of_receipt=source_of_receipt).first()
            if existing_user:
                user_id = existing_user.user_id
            else:
                user_count = CenterComponentDetail.objects.values("source_of_receipt").distinct().count() + 1
                user_id = f"USR-{user_count:03d}"
        else:
            user_id = "USR-000"

        # Create or get existing record
        obj, created = CenterComponentDetail.objects.get_or_create(
            center_id=center_id,
            component=component.strip(),
            investment_name=investment_name.strip(),
            defaults={
                "user_id": user_id,
                "center_name": center_name,
                "unit": unit,
                "scheme_name": scheme_name,
                "source_of_receipt": source_of_receipt
            }
        )

        serializer = CenterComponentDetailSerializer(obj)
        if created:
            return Response({"message": "Record created" },
                            status=status.HTTP_201_CREATED)
        else:
            return Response({"message": "Record already exists"},
                            status=status.HTTP_200_OK)

    def get(self, request):
        queryset = CenterComponentDetail.objects.all()
        serializer = CenterComponentDetailSerializer(queryset, many=True)
        return Response(serializer.data)
class ComponentInvestmentCreateAPIView(APIView):
    def post(self, request):
        serializer = ComponentInvestmentSerializer(data=request.data)
        if serializer.is_valid():
            # Check unique together
            component = serializer.validated_data["component"]
            investment_name = serializer.validated_data["investment_name"]

            obj, created = ComponentInvestment.objects.get_or_create(
                component=component,
                investment_name=investment_name
            )
            return Response(
                {"message":"Component created successfully"},
                status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    def get(self, request):
        queryset = ComponentInvestment.objects.all().order_by("-create_at")
        serializer = ComponentInvestmentSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class SchemeCreateAPIView(APIView):
    def post(self, request):
        serializer = SchemeSerializer(data=request.data)
        if serializer.is_valid():
            scheme_name = serializer.validated_data["scheme_name"]

            obj, created = Scheme.objects.get_or_create(scheme_name=scheme_name)
            return Response(
                {
                    "message":"Scheme created successfully",
                   
                },
                status=status.HTTP_201_CREATED if created else status.HTTP_200_OK
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    def get(self, request):
        queryset = Scheme.objects.all().order_by("-create_at")
        serializer = SchemeSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
class BeneficiaryRegistrationAPIView(APIView):
    def get(self, request):
        item_id = request.query_params.get("beneficiary_id")
        if item_id:
            try:
                item = BeneficiaryRegistration.objects.get(beneficiary_id=item_id)
                serializer = BeneficiaryRegistrationSerializer(item)
                return Response({"success": True, "data": serializer.data})
            except BeneficiaryRegistration.DoesNotExist:
                return Response({"success": False, "message": "Item not found"}, status=404)

        items = BeneficiaryRegistration.objects.all().order_by("-created_at")
        serializer = BeneficiaryRegistrationSerializer(items, many=True)
        return Response({"success": True, "data": serializer.data})

    
    def post(self, request):
        data = request.data.copy()

      
        scheme_name = data.get("scheme_name")
        center_name = data.get("center_name")
     
        if scheme_name:
            Scheme.objects.get_or_create(
                scheme_name=scheme_name.strip()
            )
        if center_name and not data.get("vikas_khand_name") and not data.get("vidhan_sabha_name"):
            try:
                mapping = VikasKhandVidhanSabha.objects.get(center_name=center_name)
                data["vikas_khand_name"] = mapping.vikas_khand_name
                data["vidhan_sabha_name"] = mapping.vidhan_sabha_name
            except VikasKhandVidhanSabha.DoesNotExist:
                data["vikas_khand_name"] = None
                data["vidhan_sabha_name"] = None
        serializer = BeneficiaryRegistrationSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"success": True, "message": "Beneficiary registered successfully"},
                status=201
            )
        
        return Response(
            {"success": False, "errors": serializer.errors},
            status=400
        )
    def put(self, request):
        beneficiary_id = request.data.get("beneficiary_id")

        if not beneficiary_id:
            return Response(
                {"success": False, "message": "beneficiary_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            instance = BeneficiaryRegistration.objects.get(
                beneficiary_id=beneficiary_id
            )
        except BeneficiaryRegistration.DoesNotExist:
            return Response(
                {"success": False, "message": "Beneficiary not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = BeneficiaryRegistrationSerializer(
            instance,
            data=request.data,
            partial=True  # allows partial update
        )

        if serializer.is_valid():
            instance._ip_address = get_client_ip(request)
            serializer.save()  # 🔥 triggers UPDATE signal log
            return Response(
                {"success": True, "message": "Beneficiary updated successfully"},
                status=status.HTTP_200_OK
            )

        return Response(
            {"success": False, "errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

    # ================= DELETE =================
    def delete(self, request):
        beneficiary_ids = request.data.get("beneficiary_id")
    
        if not beneficiary_ids:
            return Response(
                {"success": False, "message": "beneficiary_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
        # ✅ Convert single → list
        if isinstance(beneficiary_ids, (str, int)):
            beneficiary_ids = [beneficiary_ids]
    
        if not isinstance(beneficiary_ids, list):
            return Response(
                {"success": False, "message": "beneficiary_id must be string/int or list"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
        ip_address = get_client_ip(request)
    
        deleted_ids = []
        not_found_ids = []
    
        for b_id in beneficiary_ids:
            try:
                instance = BeneficiaryRegistration.objects.get(
                    beneficiary_id=b_id
                )
    
                # ✅ attach IP for logging
                instance._ip_address = ip_address
    
                instance.delete()
                deleted_ids.append(b_id)
    
            except BeneficiaryRegistration.DoesNotExist:
                not_found_ids.append(b_id)
    
        return Response(
            {
                "success": True,
                
                "message": f"{len(deleted_ids)} beneficiary(s) deleted successfully"
            },
            status=status.HTTP_200_OK
        )
def get_bank_details(request):
    # Get IFSC code from GET parameters
    ifsc_code = request.GET.get('ifsc_code')
    
    if not ifsc_code:
        return JsonResponse({"error": "IFSC code is required"}, status=400)
    
    url = f"https://ifsc.razorpay.com/{ifsc_code}"
    
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raises HTTPError if IFSC is invalid
        data = response.json()
        
        result = {
            "Bank": data.get("BANK"),
           
        }
        
        return JsonResponse(result)
    
    except requests.exceptions.HTTPError:
        return JsonResponse({"error": "Invalid IFSC code or API not reachable"}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
        
class GetVikasKhandByCenterAPIView(APIView):
    def get(self, request):
        center_name = request.query_params.get("center_name")

        if not center_name:
            return Response(
                {"error": "center_name query parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        queryset = VikasKhandVidhanSabha.objects.filter(
            center_name__iexact=center_name
        )

        if not queryset.exists():
            return Response(
                {"error": "No data found for this center_name"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = CenterLookupSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
        
class BillingFormFilterAPIView(APIView):

    def get(self, request):
        investment_name = request.query_params.get("investment_name", "").strip()
        sub_investment_name = request.query_params.get("sub_investment_name", "").strip()

        queryset = BillingItem.objects.all()

        def get_distinct_list(qs, field_name):
            return list(
                qs.exclude(**{f"{field_name}__isnull": True})
                  .exclude(**{f"{field_name}__exact": ""})
                  .values_list(field_name, flat=True)
                  .distinct()
            )

        global_scheme_names = list(
            Scheme.objects.values_list('scheme_name', flat=True).distinct()
        )

        global_units = get_distinct_list(queryset, "unit")

        # ==============================
        # STEP 1: INVESTMENT NAME
        # ==============================
        if not investment_name:
            return Response({
                "level": "investment_name",
                "data": get_distinct_list(queryset, "investment_name"),
                "scheme_name": global_scheme_names,
                "global_unit": global_units
            })

        queryset = queryset.filter(investment_name__iexact=investment_name)

        if not queryset.exists():
            return Response({
                "level": "investment_name",
                "data": [],
                "scheme_name": global_scheme_names,
                "global_unit": global_units
            })

        # ==============================
        # STEP 2: SUB INVESTMENT NAME
        # ==============================
        sub_investment_list = get_distinct_list(queryset, "sub_investment_name")

        if not sub_investment_name:
            return Response({
                "level": "sub_investment_name",
                "data": sub_investment_list,
                "scheme_name": global_scheme_names,
                "global_unit": global_units
            })

        queryset = queryset.filter(sub_investment_name__iexact=sub_investment_name)

        if not queryset.exists():
            return Response({
                "level": "unit",
                "data": [],
                "scheme_name": global_scheme_names,
                "global_unit": global_units
            })

        # ==============================
        # STEP 3: UNIT
        # ==============================
        return Response({
            "level": "unit",
            "data": get_distinct_list(queryset, "unit"),
            "scheme_name": global_scheme_names,
            "global_unit": global_units
        })

class RegUserPasswordUpdateAPIView(APIView):
    def put(self, request):
        user_id = request.data.get("user_id")
        user = get_object_or_404(RegUser, user_id=user_id)

        serializer = RegUserPasswordUpdateSerializer(
            user,
            data=request.data,  context={"request": request}
        )

        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Password updated successfully"},
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
@api_view(['GET'])
def reguser_list(request):

    users = RegUser.objects.exclude(user_id__isnull=True).exclude(username__isnull=True).values('user_id', 'username')
    return Response(list(users), status=status.HTTP_200_OK)


class DemandGenerationAPIView(APIView):
    def get(self, request):
        demand_id = request.query_params.get("demand_id")

        
        if demand_id:
            try:
                demand = DemandGeneration.objects.get(demand_id=demand_id)
                serializer = DemandGenerationSerializer(demand)
                return Response(serializer.data)
            except DemandGeneration.DoesNotExist:
                return Response(
                    {"error": "Demand not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
        demands = DemandGeneration.objects.all()
        serializer = DemandGenerationSerializer(demands, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = DemandGenerationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Demand created successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    def put(self, request):
        demand_id = request.data.get("demand_id")
    
        if not demand_id:
            return Response(
                {"error": "demand_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
        try:
            demand = DemandGeneration.objects.get(demand_id=demand_id)
        except DemandGeneration.DoesNotExist:
            return Response(
                {"error": "Demand not found"},
                status=status.HTTP_404_NOT_FOUND
            )
    
        demand._ip_address = get_client_ip(request)
        serializer = DemandGenerationSerializer(
            demand,
            data=request.data,
            partial=True
        )
    
        serializer.is_valid(raise_exception=True)
        serializer.save()
    
        return Response(
            {
                "message": "Demand updated successfully"
               
            },
            status=status.HTTP_200_OK
        )

    def delete(self, request):
        demand_id = request.data.get("demand_id")

        if not demand_id:
            return Response(
                {"error": "demand_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            demand = DemandGeneration.objects.get(demand_id=demand_id)
        except DemandGeneration.DoesNotExist:
            return Response(
                {"error": "Demand not found"},
                status=status.HTTP_200_OK
            )
        ip = get_client_ip(request)

       
        centers = demand.demand_centers.all()
        for center in centers:
            center._ip_address = ip
            center.delete() 

        # optional: log parent IP also
        demand._ip_address = ip

        demand.delete()
        
        return Response(
            {"message": "Demand deleted successfully"},
            status=status.HTTP_200_OK
        )
class DemandByCenterAPIView(APIView):

    def get(self, request):
        demand_id = request.query_params.get("demand_id")

        if demand_id:
            centers = DemandByCenter.objects.filter(demand_id__demand_id=demand_id)
        else:
            centers = DemandByCenter.objects.all()

        serializer = DemandByCenterSerializer(centers, many=True)
        return Response(serializer.data)

  
    def post(self, request):
        demand_id_value = request.data.get("demand_id")

        if not demand_id_value:
            return Response(
                {"error": "demand_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            demand = DemandGeneration.objects.get(demand_id=demand_id_value)
        except DemandGeneration.DoesNotExist:
            return Response(
                {"error": "Invalid demand_id"},
                status=status.HTTP_404_NOT_FOUND
            )

        data = request.data.copy()
        data["demand_id"] = demand.demand_id   # FK expects object/PK

        serializer = DemandByCenterSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "DemandByCenter created successfully"}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    def put(self, request):
        record_id = request.data.get("id")

        if not record_id:
            return Response(
                {"error": "id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            demand_center = DemandByCenter.objects.get(id=record_id)
        except DemandByCenter.DoesNotExist:
            return Response(
                {"error": "Record not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        demand_center._ip_address = get_client_ip(request)

        serializer = DemandByCenterSerializer(
            demand_center,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "DemandByCenter updated successfully"},
                status=status.HTTP_200_OK
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
    def delete(self, request):
        record_id = request.data.get("id")

        if not record_id:
            return Response(
                {"error": "id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            demand_center = DemandByCenter.objects.get(id=record_id)
        except DemandByCenter.DoesNotExist:
            return Response(
                {"error": "Record not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        demand_center.delete()

        return Response(
            {"message": "DemandByCenter deleted successfully"},
            status=status.HTTP_200_OK
        )
class NurseryFinancialAPIView(APIView):

    def get(self, request):
        records = NurseryFinancial.objects.all().order_by("-created_at")
        serializer = NurseryFinancialSerializer(records, many=True)
        return Response(serializer.data)

    def post(self, request):
        data = request.data.copy()

        nursery_name = data.get("nursery_name")
        standard_item = data.get("standard_item")

        if not nursery_name or not standard_item:
            return Response(
                {"error": "nursery_name and standard_item are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        existing_record = NurseryFinancial.objects.filter(
            nursery_name=nursery_name,
            standard_item=standard_item
        ).first()

        # ---------------------------
        # IF RECORD EXISTS → UPDATE
        # ---------------------------
        if existing_record:

            allocated = data.get("allocated_amount")
            spent = data.get("spent_amount")

            if allocated:
                existing_record.allocated_amount = (
                    (existing_record.allocated_amount or Decimal("0.00"))
                    + Decimal(allocated)
                )

            if spent:
                existing_record.spent_amount = (
                    (existing_record.spent_amount or Decimal("0.00"))
                    + Decimal(spent)
                )

            # Replace fields
            existing_record.description = data.get("description")
            existing_record.registration_date = data.get("registration_date")

            existing_record.save()

            return Response(
                {"message": "Nursery financial record updated successfully"},
                status=status.HTTP_200_OK
            )

        # ---------------------------
        # IF NOT EXISTS → CREATE
        # ---------------------------
        serializer = NurseryFinancialSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Nursery financial record created successfully"},
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        record_id = request.data.get("id")

        if not record_id:
            return Response(
                {"error": "id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            record = NurseryFinancial.objects.get(id=record_id)
        except NurseryFinancial.DoesNotExist:
            return Response(
                {"error": "Record not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        data = request.data.copy()
        data.pop("id", None)

        record._ip_address = get_client_ip(request)

        for field in record._meta.fields:
            field_name = field.name
            if field_name in data:
                setattr(record, field_name, data.get(field_name))

        record.save()  
        return Response(
            {"message": "Nursery financial record updated successfully"},
            status=status.HTTP_200_OK
        )
    def delete(self, request):
        ids = request.data.get("id")
    
        if not ids:
            return Response(
                {"success": False, "message": "id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
        # ✅ Convert single → list
        if isinstance(ids, int):
            ids = [ids]
    
        if not isinstance(ids, list):
            return Response(
                {"success": False, "message": "id must be int or list"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
        ip_address = get_client_ip(request)
    
        deleted_ids = []
        not_found_ids = []
    
        for record_id in ids:
            try:
                record = NurseryFinancial.objects.get(id=record_id)
    
                # ✅ attach IP for logging
                record._ip_address = ip_address
    
                record.delete()
                deleted_ids.append(record_id)
    
            except NurseryFinancial.DoesNotExist:
                not_found_ids.append(record_id)
    
        return Response(
            {
                "success": True,
               
                "message": f"{len(deleted_ids)} record(s) deleted successfully"
            },
            status=status.HTTP_200_OK
        )
class NurseryPhysicalAPIView(APIView):

    def get(self, request):
        nursery_id = request.query_params.get("id")

        if nursery_id:
            try:
                nursery = NurseryPhysical.objects.get(id=nursery_id)
                serializer = NurseryPhysicalSerializer(nursery)
                return Response(serializer.data)
            except NurseryPhysical.DoesNotExist:
                return Response(
                    {"error": "Nursery record not found"},
                    status=status.HTTP_404_NOT_FOUND
                )

        nurseries = NurseryPhysical.objects.all()
        serializer = NurseryPhysicalSerializer(nurseries, many=True)
        return Response(serializer.data)


    def post(self, request):
        serializer = NurseryPhysicalSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "NurseryPhysical created successfully"},
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def put(self, request):
        nursery_id = request.data.get("id")

        if not nursery_id:
            return Response(
                {"error": "id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            nursery = NurseryPhysical.objects.get(id=nursery_id)
        except NurseryPhysical.DoesNotExist:
            return Response(
                {"error": "Nursery record not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = NurseryPhysicalSerializer(
            nursery,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "NurseryPhysical updated successfully"},
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def delete(self, request):
        ids = request.data.get("id")

        if not ids:
            return Response(
                {"success": False, "message": "id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ✅ Convert single → list
        if isinstance(ids, int):
            ids = [ids]

        if not isinstance(ids, list):
            return Response(
                {"success": False, "message": "id must be int or list"},
                status=status.HTTP_400_BAD_REQUEST
            )

        deleted_count = 0

        for nursery_id in ids:
            try:
                nursery = NurseryPhysical.objects.get(id=nursery_id)
                nursery.delete()
                deleted_count += 1
            except NurseryPhysical.DoesNotExist:
                continue  # skip invalid ids

        return Response(
            {
                "success": True,
                "message": f"{deleted_count} record(s) deleted successfully"
            },
            status=status.HTTP_200_OK
        )
class NurseryPhysicalRecipientAPIView(APIView):

    def get(self, request):
        nursery_id = request.query_params.get("nursery_id")

        if nursery_id:
            recipients = NurseryPhysicalRecipient.objects.filter(
                nursery_physical__id=nursery_id
            )
        else:
            recipients = NurseryPhysicalRecipient.objects.all()

        serializer = NurseryPhysicalRecipientSerializer(recipients, many=True)
        return Response(serializer.data)


    def post(self, request):
        nursery_id = request.data.get("nursery_physical")

        if not nursery_id:
            return Response(
                {"error": "nursery_physical id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            nursery = NurseryPhysical.objects.get(id=nursery_id)
        except NurseryPhysical.DoesNotExist:
            return Response(
                {"error": "Invalid nursery id"},
                status=status.HTTP_404_NOT_FOUND
            )

        data = request.data.copy()
        data["nursery_physical"] = nursery.id

        serializer = NurseryPhysicalRecipientSerializer(data=data)

        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Recipient created successfully"},
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def put(self, request):
        record_id = request.data.get("id")

        if not record_id:
            return Response(
                {"error": "id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            recipient = NurseryPhysicalRecipient.objects.get(id=record_id)
        except NurseryPhysicalRecipient.DoesNotExist:
            return Response(
                {"error": "Record not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = NurseryPhysicalRecipientSerializer(
            recipient,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Recipient updated successfully"},
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


    def delete(self, request):
        record_id = request.data.get("id")

        if not record_id:
            return Response(
                {"error": "id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            recipient = NurseryPhysicalRecipient.objects.get(id=record_id)
        except NurseryPhysicalRecipient.DoesNotExist:
            return Response(
                {"error": "Record not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        recipient.delete()

        return Response(
            {"message": "Recipient deleted successfully"},
            status=status.HTTP_200_OK
        )

class UpdateBillingReportAPIView(APIView):

    def put(self, request):
        serializer = BillingReportUpdateSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        data = serializer.validated_data

        old_bill_report_id = data["old_bill_report_id"]
        new_bill_report_id = data.get("new_bill_report_id")
        billing_date = data.get("billing_date")
        status_value = data.get("status")
        multiple_bills = data.get("multiple_bills", [])
        component_pageno = data.get("component_pageno")
        try:
            report = BillingReport.objects.get(
                bill_report_id=old_bill_report_id
            )
        except BillingReport.DoesNotExist:
            return Response(
                {"error": "Report not found"},
                status=404
            )

        if (
            new_bill_report_id
            and new_bill_report_id != old_bill_report_id
            and BillingReport.objects.filter(
                bill_report_id=new_bill_report_id
            ).exists()
        ):
            return Response(
                {"error": "bill_report_id already exists"},
                status=400
            )

        with transaction.atomic():

            if new_bill_report_id:
                report.bill_report_id = new_bill_report_id

            if billing_date:
                report.billing_date = billing_date

            if status_value:
                report.status = status_value
                
            if component_pageno is not None:
                report.component_pageno = component_pageno

            component_list = []

            center_items = BillingItem.objects.filter(
                center_id=report.center_id
            )

            for bill in multiple_bills:

                item = center_items.filter(
                    bill_id=bill["bill_id"]
                ).first()

                if not item:
                    continue

                updated_qty = bill["updated_quantity"]

                item.updated_quantity = updated_qty

                # ==========================================
                # BILL RATE ACCORDING TO SCHEME
                # ==========================================

                scheme_name = (item.scheme_name or "").strip()

                selling_rate_schemes = [
                    "4401 बिक्री हेतु",
                    "मुख्यमंत्री एकीकृत विकास योजना"
                ]

                if scheme_name in selling_rate_schemes:
                    bill_rate = item.farmer_selling_rate or 0
                else:
                    bill_rate = item.farmer_subsidy_rate or 0

                item.rate = bill_rate

                item.save(
                    update_fields=[
                        "updated_quantity",
                        "rate"
                    ]
                )

                allocated_qty = float(
                    item.allocated_quantity or 0
                )

                rate = float(
                    item.rate or 0
                )

                buy_amount = allocated_qty * rate
                sold_amount = float(updated_qty) * rate

                component_list.append([
                    str(item.bill_id),
                    str(item.sub_investment_name),
                    str(item.investment_name),
                    str(item.unit),
                    str(allocated_qty),
                    str(rate),
                    str(updated_qty),
                    str(buy_amount),
                    str(sold_amount),
                    str(item.source_of_receipt),
                    str(item.scheme_name),
                ])

            if component_list:
                report.component_data = component_list
            
            report.save()

            pdf_url = generate_billing_report_pdf(report)

        return Response(
            {
                "success": True,
                "message": "Billing report updated successfully",
                "bill_report_id": report.bill_report_id,
                "billing_date": report.billing_date,
                "status": report.status,
                "pdf_file": pdf_url,
            },
            status=200,
        )


        
class DownloadMultipleReceiptsAPIView(APIView):

    def post(self, request):
        bill_report_ids = request.data.get("bill_report_ids", [])

        if not isinstance(bill_report_ids, list) or not bill_report_ids:
            return Response(
                {"status": False, "message": "bill_report_ids must be a list."},
                status=400
            )

        reports = BillingReport.objects.filter(
            bill_report_id__in=bill_report_ids
        ).exclude(recipt_file="").exclude(recipt_file__isnull=True)

        if not reports.exists():
            return Response(
                {"status": False, "message": "No receipt files found."},
                status=404
            )

        temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")

        with zipfile.ZipFile(temp_zip.name, "w", zipfile.ZIP_DEFLATED) as zipf:
            for report in reports:
                if report.recipt_file and os.path.exists(report.recipt_file.path):
                    zipf.write(
                        report.recipt_file.path,
                        arcname=f"{report.bill_report_id}_{os.path.basename(report.recipt_file.path)}"
                    )

        temp_zip.close()

        response = FileResponse(
            open(temp_zip.name, "rb"),
            content_type="application/zip",
            as_attachment=True,
            filename="billing_receipts.zip",
        )

        response["Content-Length"] = os.path.getsize(temp_zip.name)
        response["Content-Disposition"] = 'attachment; filename="billing_receipts.zip"'

        return response
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
###########3OTHER PART#####################


from rest_framework import status, viewsets
from rest_framework.response import Response

from .models import (
    UdyanCropStandard,
    UdyanBill,
)

from .serializers import (
    UdyanCropStandardSerializer,
    UdyanBillSerializer,
)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import UdyanCropStandard, UdyanBill
from .serializers import (
    UdyanCropStandardSerializer,
    UdyanBillSerializer
)


# =========================================================
# UDYAN CROP STANDARD - LIST & CREATE
# =========================================================

class UdyanCropStandardAPIView(APIView):

    def get(self, request):

        queryset = UdyanCropStandard.objects.all()

        financial_year = request.query_params.get(
            "financial_year"
        )

        if financial_year:
            queryset = queryset.filter(
                financial_year=financial_year
            )

        queryset = queryset.order_by("crop_name")

        serializer = UdyanCropStandardSerializer(
            queryset,
            many=True
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    def post(self, request):

        serializer = UdyanCropStandardSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        crop = serializer.save()

        return Response(
            UdyanCropStandardSerializer(crop).data,
            status=status.HTTP_201_CREATED
        )


# =========================================================
# UDYAN CROP STANDARD - DETAIL / UPDATE / DELETE
# =========================================================

class UdyanCropStandardDetailAPIView(APIView):

    def get_object(self, pk):

        try:
            return UdyanCropStandard.objects.get(
                pk=pk,
                is_active=True
            )

        except UdyanCropStandard.DoesNotExist:
            return None

    def get(self, request):

        queryset = UdyanCropStandard.objects.all()

        financial_year = request.query_params.get(
            "financial_year"
        )

        if financial_year:
            queryset = queryset.filter(
                financial_year=financial_year
            )

        queryset = queryset.order_by("crop_name")

        serializer = UdyanCropStandardSerializer(
            queryset,
            many=True
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    def put(self, request, pk):

        crop = self.get_object(pk)

        if not crop:
            return Response(
                {
                    "success": False,
                    "message": "Crop standard not found"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = UdyanCropStandardSerializer(
            crop,
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        crop = serializer.save()

        return Response(
            UdyanCropStandardSerializer(crop).data,
            status=status.HTTP_200_OK
        )

    def patch(self, request, pk):

        crop = self.get_object(pk)

        if not crop:
            return Response(
                {
                    "success": False,
                    "message": "Crop standard not found"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = UdyanCropStandardSerializer(
            crop,
            data=request.data,
            partial=True
        )

        serializer.is_valid(
            raise_exception=True
        )

        crop = serializer.save()

        return Response(
            UdyanCropStandardSerializer(crop).data,
            status=status.HTTP_200_OK
        )

    def delete(self, request, pk):

        crop = self.get_object(pk)

        if not crop:
            return Response(
                {
                    "success": False,
                    "message": "Crop standard not found"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        crop.delete()

        return Response(
            {
                "success": True,
                "message": "Crop standard deleted successfully"
            },
            status=status.HTTP_204_NO_CONTENT
        )


# =========================================================
# UDYAN BILL - LIST & CREATE
# =========================================================

class UdyanBillAPIView(APIView):

    def get(self, request):
        center = request.query_params.get("center")

        bills = UdyanBill.objects.select_related(
            "crop"
        ).prefetch_related(
            "items"
        ).all()

        # Filter by center only if provided
        if center:
            bills = bills.filter(center=center)

        serializer = UdyanBillSerializer(
            bills,
            many=True
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    def post(self, request):

        serializer = UdyanBillSerializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        bill = serializer.save()

        return Response(
            UdyanBillSerializer(bill).data,
            status=status.HTTP_201_CREATED
        )


# =========================================================
# UDYAN BILL - DETAIL / UPDATE / DELETE
# =========================================================

class UdyanBillDetailAPIView(APIView):

    def get_object(self, pk):

        try:
            return UdyanBill.objects.select_related(
                "crop"
            ).prefetch_related(
                "items"
            ).get(pk=pk)

        except UdyanBill.DoesNotExist:
            return None

    def get(self, request, pk):

        bill = self.get_object(pk)

        if not bill:
            return Response(
                {
                    "success": False,
                    "message": "Bill not found"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = UdyanBillSerializer(bill)

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    def put(self, request, pk):

        bill = self.get_object(pk)

        if not bill:
            return Response(
                {
                    "success": False,
                    "message": "Bill not found"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = UdyanBillSerializer(
            bill,
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        bill = serializer.save()

        return Response(
            UdyanBillSerializer(bill).data,
            status=status.HTTP_200_OK
        )

    def patch(self, request, pk):

        bill = self.get_object(pk)

        if not bill:
            return Response(
                {
                    "success": False,
                    "message": "Bill not found"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = UdyanBillSerializer(
            bill,
            data=request.data,
            partial=True
        )

        serializer.is_valid(
            raise_exception=True
        )

        bill = serializer.save()

        return Response(
            UdyanBillSerializer(bill).data,
            status=status.HTTP_200_OK
        )

    def delete(self, request, pk):

        bill = self.get_object(pk)

        if not bill:
            return Response(
                {
                    "success": False,
                    "message": "Bill not found"
                },
                status=status.HTTP_404_NOT_FOUND
            )

        bill.delete()

        return Response(
            {
                "success": True,
                "message": "Bill deleted successfully"
            },
            status=status.HTTP_204_NO_CONTENT
        )
        
        
        
        
        
        

from decimal import Decimal

from django.db.models import Sum

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import (
    ListAPIView,
    RetrieveUpdateAPIView,
    ListCreateAPIView,
    DestroyAPIView,
)

from .models import (
    BeejMasterSetting,
    BeejCentre,
    BeejVariety,
    BeejStandard,
    BeejPurchase,
    BeejAllocation,
    BeejFarmerDistribution,
)

from .serializers import (
    MasterSettingSerializer,
    CentreSerializer,
    VarietySerializer,
    StandardSerializer,
    PurchaseSerializer,
    AllocationSerializer,
    DistributionSerializer,
)


DEFAULT_CENTRES = list(
    VikasKhandVidhanSabha.objects
    .values_list("center_name", flat=True)
    .distinct()
)


DEFAULT_VARIETIES = [
    (
        "ब्रोकली Rock 001",
        "सा0जाति",
        95600,
    ),
    (
        "बैंगन BSHB-33 (Navin)",
        "अनु0जाति",
        14400,
    ),
    (
        "टमाटर BSHT-10 (Amol)",
        "सा0जाति",
        87450,
    ),
    (
        "टमाटर Sindhu",
        "सा0जाति",
        98000,
    ),
    (
        "शिमला मिर्च BSCH-888 (Indu)",
        "सा0जाति",
        99000,
    ),
    (
        "शिमला मिर्च Alaska",
        "सा0जाति",
        125000,
    ),
    (
        "बंदगोभी BSCB-01 (Coral)",
        "सा0जाति",
        58400,
    ),
    (
        "बंदगोभी Bajwa60",
        "सा0जाति",
        47900,
    ),
    (
        "फूलगोभी BSCF-11 (Mansi)",
        "अनु0जाति",
        59500,
    ),
    (
        "फूलगोभी AZCL-900",
        "सा0जाति",
        57200,
    ),
]


DEFAULT_PURCHASES = [
    (
        "टमाटर BSHT-10 (Amol)",
        "2026-05-15",
        "Anishree Traders",
        87450,
        2.80,
        "देयक सं0 90",
    ),
    (
        "टमाटर Sindhu",
        "2026-05-15",
        "Devbhoomi Farming Solutions",
        98000,
        2.55,
        "देयक सं0 86",
    ),
    (
        "ब्रोकली Rock 001",
        "2026-05-15",
        "Devbhoomi Farming Solutions",
        95600,
        1.00,
        "देयक सं0 113",
    ),
    (
        "बैंगन BSHB-33 (Navin)",
        "2026-05-15",
        "Devbhoomi Farming Solutions",
        14400,
        10.70,
        "देयक सं0 113",
    ),
    (
        "शिमला मिर्च BSCH-888 (Indu)",
        "2026-05-15",
        "NIRVANA IRRIGATION",
        99000,
        2.52,
        "देयक सं0 65",
    ),
    (
        "शिमला मिर्च Alaska",
        "2026-05-15",
        "Anishree Traders",
        125000,
        2.00,
        "देयक सं0 81",
    ),
    (
        "फूलगोभी AZCL-900",
        "2026-05-22",
        "NIRVANA IRRIGATION",
        57200,
        4.37,
        "देयक सं0 116",
    ),
    (
        "फूलगोभी BSCF-11 (Mansi)",
        "2026-05-22",
        "Devbhoomi Farming Solutions",
        59500,
        4.20,
        "देयक सं0 182",
    ),
    (
        "बंदगोभी Bajwa60",
        "2026-05-22",
        "Anishree Traders",
        47900,
        5.21,
        "देयक सं0 138",
    ),
    (
        "बंदगोभी BSCB-01 (Coral)",
        "2026-05-22",
        "NIRVANA IRRIGATION",
        58400,
        4.28,
        "देयक सं0 177",
    ),
]


ALLOT = {
    "ब्रोकली Rock 001": [
        40, 40, 40, 40, 40, 40,
        40, 40, 40, 40, 40, 40,
        40, 40, 40, 40, 40, 40,
        40, 40, 40, 80, 40, 40,
    ],

    "बैंगन BSHB-33 (Navin)": [
        500, 500, 500, 500, 500, 500,
        500, 500, 500, 200, 200, 200,
        500, 500, 500, 500, 200, 400,
        500, 500, 500, 500, 500, 500,
    ],

    "टमाटर BSHT-10 (Amol)": [
        240, 240, 240, 240, 240, 240,
        240, 240, 240, 200, 200, 240,
        0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0,
    ],

    "टमाटर Sindhu": [
        0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0,
        200, 200, 200, 200, 200, 200,
        200, 200, 200, 350, 200, 200,
    ],

    "शिमला मिर्च BSCH-888 (Indu)": [
        320, 200, 200, 200, 200, 200,
        200, 200, 200, 200, 200, 200,
        0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0,
    ],

    "शिमला मिर्च Alaska": [
        0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0,
        160, 160, 160, 160, 160, 160,
        160, 160, 160, 240, 160, 160,
    ],

    "बंदगोभी BSCB-01 (Coral)": [
        350, 350, 430, 350, 350, 350,
        350, 350, 350, 350, 350, 350,
        0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0,
    ],

    "बंदगोभी Bajwa60": [
        0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0,
        420, 420, 420, 420, 420, 420,
        420, 420, 420, 420, 590, 420,
    ],

    "फूलगोभी BSCF-11 (Mansi)": [
        440, 460, 330, 330, 330, 330,
        330, 330, 330, 330, 330, 330,
        0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0,
    ],

    "फूलगोभी AZCL-900": [
        0, 0, 0, 0, 0, 0,
        0, 0, 0, 0, 0, 0,
        330, 330, 330, 330, 330, 330,
        330, 330, 330, 630, 440, 330,
    ],
}


def ensure_defaults():

    # Existing database should NEVER be reseeded.
    if BeejCentre.objects.exists():
        return

    master, _ = (
        BeejMasterSetting.objects.get_or_create(
            financial_year="2026-27",
            defaults={
                "purchase_limit": 250000,
                "project_cost": 60000,
                "max_subsidy": 30000,
                "farmer_share": 30000,
            },
        )
    )

    for name in DEFAULT_CENTRES:
        BeejCentre.objects.create(
            name=name
        )

    varieties = {}

    for (
        name,
        jati,
        rate,
    ) in DEFAULT_VARIETIES:

        varieties[name] = (
            BeejVariety.objects.create(
                name=name,
                jati=jati,
                default_rate=rate,
            )
        )

    for (
        name,
        jati,
        rate,
    ) in DEFAULT_VARIETIES:

        variety = varieties[name]

        BeejStandard.objects.create(
            variety=variety,

            item1_qty=1,
            item1_rate=8700,

            item2_qty=Decimal("30000") / Decimal(
                str(rate)
            ),

            item2_rate=rate,

            item3_qty=100,
            item3_rate=150,

            item4_qty=20,
            item4_rate=315,
        )

    for (
        variety_name,
        date,
        supplier,
        rate,
        qty,
        ref,
    ) in DEFAULT_PURCHASES:

        BeejPurchase.objects.create(
            date=date,

            variety=varieties[
                variety_name
            ],

            supplier=supplier,

            qty_kg=qty,

            rate=rate,

            ref=ref,
        )

    centres = list(
        BeejCentre.objects
        .order_by("id")
    )

    for (
        variety_name,
        quantities,
    ) in ALLOT.items():

        variety = varieties[
            variety_name
        ]

        standard = variety.standard

        for index, qty in enumerate(
            quantities
        ):

            if qty <= 0:
                continue

            area = (
                Decimal(
                    str(qty)
                )
                / standard.seed_gm_per_hectare
            )

            BeejAllocation.objects.create(
                date="2026-06-01",

                centre=centres[index],

                variety=variety,

                qty_gm=qty,

                area=area,

                project_cost=area * master.project_cost,

                subsidy=area * master.max_subsidy,

                farmer_share=area * master.farmer_share,

                source="आवंटन पत्र जिला यो0-सब्जी/2026-27",
            )


from rest_framework.views import APIView
from rest_framework.generics import (
    ListAPIView,
    RetrieveUpdateAPIView,
    ListCreateAPIView,
    DestroyAPIView,
)
from rest_framework.response import Response


class BootstrapAPIView(APIView):

    def get(self, request):
        ensure_defaults()

        master = BeejMasterSetting.objects.get(
            financial_year="2026-27"
        )

        return Response({
            "master": MasterSettingSerializer(
                master
            ).data,

            "centres": CentreSerializer(
                BeejCentre.objects.filter(
                    is_active=True
                ),
                many=True
            ).data,

            "varieties": VarietySerializer(
                BeejVariety.objects.filter(
                    is_active=True
                ),
                many=True
            ).data,

            "standards": StandardSerializer(
                BeejStandard.objects
                .select_related("variety")
                .all(),
                many=True
            ).data,

            "purchases": PurchaseSerializer(
                BeejPurchase.objects
                .select_related("variety")
                .all(),
                many=True
            ).data,

            "allocations": AllocationSerializer(
                BeejAllocation.objects
                .select_related(
                    "centre",
                    "variety"
                )
                .all(),
                many=True
            ).data,

            "entries": DistributionSerializer(
                BeejFarmerDistribution.objects
                .select_related(
                    "centre",
                    "variety"
                )
                .all(),
                many=True
            ).data,
        })


class MasterSettingAPIView(APIView):

    def get(self, request):
        ensure_defaults()

        master = BeejMasterSetting.objects.get(
            financial_year="2026-27"
        )

        return Response(
            MasterSettingSerializer(master).data
        )

    def put(self, request):
        ensure_defaults()

        master = BeejMasterSetting.objects.get(
            financial_year="2026-27"
        )

        serializer = MasterSettingSerializer(
            master,
            data=request.data,
            partial=True
        )

        serializer.is_valid(
            raise_exception=True
        )

        serializer.save(
            financial_year="2026-27"
        )

        return Response(serializer.data)


class CentreListAPIView(ListAPIView):

    serializer_class = CentreSerializer

    queryset = BeejCentre.objects.filter(
        is_active=True
    )


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from .models import BeejVariety
from .serializers import VarietySerializer


class VarietyListAPIView(APIView):

    def get(self, request):
        varieties = BeejVariety.objects.filter(
            is_active=True
        )

        serializer = VarietySerializer(
            varieties,
            many=True
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    def post(self, request):
        serializer = VarietySerializer(
            data=request.data
        )

        if serializer.is_valid():
            serializer.save()

            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class VarietyDetailAPIView(APIView):

    def get_object(self, pk):
        return get_object_or_404(
            BeejVariety,
            pk=pk,
            is_active=True
        )

    def put(self, request, pk):
        variety = self.get_object(pk)

        serializer = VarietySerializer(
            variety,
            data=request.data
        )

        if serializer.is_valid():
            serializer.save()

            return Response(
                serializer.data,
                status=status.HTTP_200_OK
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    def delete(self, request, pk):
        variety = self.get_object(pk)

        variety.is_active = False
        variety.save(update_fields=["is_active"])

        return Response(
            {
                "status": True,
                "message": "Variety deleted successfully"
            },
            status=status.HTTP_200_OK
        )

class StandardListAPIView(APIView):

    def get(self, request):
        standards = BeejStandard.objects.select_related("variety").all()
        serializer = StandardSerializer(standards, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = StandardSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class StandardDetailAPIView(APIView):

    def get_object(self, pk):
        return get_object_or_404(
            BeejStandard.objects.select_related("variety"),
            pk=pk
        )

    def get(self, request, pk):
        standard = self.get_object(pk)
        serializer = StandardSerializer(standard)
        return Response(serializer.data)

    def put(self, request, pk):
        standard = self.get_object(pk)
        serializer = StandardSerializer(
            standard,
            data=request.data
        )
    
        if serializer.is_valid():
            serializer.save()
            return Response({
                "status": True,
                "message": "Standard updated successfully",
                "data": serializer.data
            })
    
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
    
    
    def delete(self, request, pk):
        standard = self.get_object(pk)
        standard.delete()
    
        return Response(
            {
                "status": True,
                "message": "Standard deleted successfully"
            },
            status=status.HTTP_200_OK
        )

class PurchaseListCreateAPIView(ListCreateAPIView):

    serializer_class = PurchaseSerializer

    queryset = (
        BeejPurchase.objects
        .select_related("variety")
        .all()
    )


class PurchaseDetailAPIView(DestroyAPIView):

    serializer_class = PurchaseSerializer

    queryset = BeejPurchase.objects.all()


class AllocationListCreateAPIView(ListCreateAPIView):

    serializer_class = AllocationSerializer

    queryset = (
        BeejAllocation.objects
        .select_related(
            "centre",
            "variety"
        )
        .all()
    )


class AllocationDetailAPIView(DestroyAPIView):

    serializer_class = AllocationSerializer

    queryset = BeejAllocation.objects.all()


class DistributionListCreateAPIView(ListCreateAPIView):

    serializer_class = DistributionSerializer

    queryset = (
        BeejFarmerDistribution.objects
        .select_related(
            "centre",
            "variety"
        )
        .all()
    )


class DistributionDetailAPIView(DestroyAPIView):

    serializer_class = DistributionSerializer

    queryset = BeejFarmerDistribution.objects.all()
    
    
    
    
    
    
    
    
    
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

from .models import LibraryCategory, LibraryDocument
from .serializers import (
    LibraryCategorySerializer,
    LibraryDocumentSerializer
)


# =========================================================
# CATEGORY LIST + CREATE
# =========================================================

class LibraryCategoryListCreateView(APIView):

    def get(self, request):

        categories = LibraryCategory.objects.all().order_by("-created_at")

        serializer = LibraryCategorySerializer(
            categories,
            many=True
        )

        return Response(
            {
                "status": True,
                "message": "Categories fetched successfully",
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )

    def post(self, request):

        serializer = LibraryCategorySerializer(
            data=request.data
        )

        if serializer.is_valid():

            category = serializer.save()

            return Response(
                {
                    "status": True,
                    "message": "Category created successfully",
                    "data": LibraryCategorySerializer(
                        category
                    ).data
                },
                status=status.HTTP_201_CREATED
            )

        return Response(
            {
                "status": False,
                "message": "Validation error",
                "errors": serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )


# =========================================================
# CATEGORY DETAIL
# =========================================================

class LibraryCategoryDetailView(APIView):

    def get(self, request, pk):

        category = get_object_or_404(
            LibraryCategory,
            id=pk
          
        )

        serializer = LibraryCategorySerializer(category)

        return Response(
            {
                "status": True,
                "message": "Category fetched successfully",
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )

    def put(self, request, pk):

        category = get_object_or_404(
            LibraryCategory,
            id=pk
        )

        serializer = LibraryCategorySerializer(
            category,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():

            serializer.save()

            return Response(
                {
                    "status": True,
                    "message": "Category updated successfully",
                    "data": serializer.data
                },
                status=status.HTTP_200_OK
            )

        return Response(
            {
                "status": False,
                "message": "Validation error",
                "errors": serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    def delete(self, request, pk):

        category = get_object_or_404(
            LibraryCategory,
            id=pk
        )

        category.is_active = False
        category.delete()

        return Response(
            {
                "status": True,
                "message": "Category deleted successfully"
            },
            status=status.HTTP_200_OK
        )


# =========================================================
# DOCUMENT LIST + CREATE
# =========================================================

class LibraryDocumentListCreateView(APIView):

    def get(self, request):

        category_id = request.query_params.get("category")

        documents = LibraryDocument.objects.all()

        if category_id:
            documents = documents.filter(
                category_id=category_id
            )

        serializer = LibraryDocumentSerializer(
            documents,
            many=True
        )

        return Response(
            {
                "status": True,
                "message": "Documents fetched successfully",
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )

    def post(self, request):

        category_id = request.data.get("category")

        if not category_id:

            return Response(
                {
                    "status": False,
                    "message": "Category is required."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        category = get_object_or_404(
            LibraryCategory,
            id=category_id,
            is_active=True
        )

        serializer = LibraryDocumentSerializer(
            data=request.data
        )

        if serializer.is_valid():

            document = serializer.save(
                category=category
            )

            return Response(
                {
                    "status": True,
                    "message": "Document uploaded successfully",
                    "data": LibraryDocumentSerializer(
                        document
                    ).data
                },
                status=status.HTTP_201_CREATED
            )

        return Response(
            {
                "status": False,
                "message": "Validation error",
                "errors": serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )


# =========================================================
# DOCUMENT DETAIL
# =========================================================

class LibraryDocumentDetailView(APIView):

    def get(self, request, pk):

        document = get_object_or_404(
            LibraryDocument,
            id=pk,
            is_active=True
        )

        serializer = LibraryDocumentSerializer(document)

        return Response(
            {
                "status": True,
                "message": "Document fetched successfully",
                "data": serializer.data
            },
            status=status.HTTP_200_OK
        )

    def put(self, request, pk):

        document = get_object_or_404(
            LibraryDocument,
            id=pk
        )

        serializer = LibraryDocumentSerializer(
            document,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():

            serializer.save()

            return Response(
                {
                    "status": True,
                    "message": "Document updated successfully",
                    "data": serializer.data
                },
                status=status.HTTP_200_OK
            )

        return Response(
            {
                "status": False,
                "message": "Validation error",
                "errors": serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )

    def delete(self, request, pk):

        document = get_object_or_404(
            LibraryDocument,
            id=pk
        )

        document.is_active = False
        
        document.delete()

        return Response(
            {
                "status": True,
                "message": "Document deleted successfully"
            },
            status=status.HTTP_200_OK
        )
        
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import MonthReport
from .serializers import MonthReportSerializer


class MonthReportListAPIView(APIView):

    def get(self, request):
        reports = MonthReport.objects.all().order_by("-financial_year", "-month")
        serializer = MonthReportSerializer(reports, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = MonthReportSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MonthReportDetailAPIView(APIView):

    def get_object(self, pk):
        try:
            return MonthReport.objects.get(pk=pk)
        except MonthReport.DoesNotExist:
            return None

    def get(self, request, pk):
        try:
            report = MonthReport.objects.get(pk=pk)
        except MonthReport.DoesNotExist:
            return JsonResponse(
                {"error": "Month report not found."},
                status=404
            )

        if not report.month_report:
            return JsonResponse(
                {"error": "Excel file is not available for this report."},
                status=404
            )

        file_path = report.month_report.path

        if not os.path.exists(file_path):
            return JsonResponse(
                {
                    "error": "Excel file does not exist on the server.",
                    "path": file_path
                },
                status=404
            )

        response = FileResponse(
            open(file_path, "rb"),
            content_type=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            )
        )

        response["Content-Disposition"] = (
            f'inline; filename="{os.path.basename(file_path)}"'
        )

        response["Access-Control-Allow-Origin"] = "http://localhost:3000"

        return response

    def put(self, request, pk):
        report = self.get_object(pk)

        if not report:
            return Response(
                {"detail": "Month report not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = MonthReportSerializer(report, data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        report = self.get_object(pk)

        if not report:
            return Response(
                {"detail": "Month report not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        report.delete()

        return Response(
            {"message": "Month report deleted successfully."},
            status=status.HTTP_204_NO_CONTENT
        )
       
       
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import KisanPersonalLandDetails, KisanPlanTechnicalBankDetails, KisanApplicationDocuments
from .serializers import KisanPersonalLandDetailsSerializer, KisanPlanTechnicalBankDetailsSerializer, KisanApplicationDocumentsSerializer


class KisanApplicationAPIView(APIView):

    @transaction.atomic
    def post(self, request):
        serializer = KisanPersonalLandDetailsSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({"success": False, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        personal = serializer.save()
        form_id = personal.form_id
        plan = KisanPlanTechnicalBankDetails.objects.get(form_id=form_id)
        application = KisanApplicationDocuments.objects.get(form_id=form_id)

        return Response({
            "success": True,
            "message": "Kisan application created successfully.",
            "form_id": form_id,
            "data": {
                "personal": KisanPersonalLandDetailsSerializer(personal).data,
                "plan_technical_bank": KisanPlanTechnicalBankDetailsSerializer(plan).data,
                "application_documents": KisanApplicationDocumentsSerializer(application).data
            }
        }, status=status.HTTP_201_CREATED)

    def get(self, request):
        form_id = request.query_params.get("form_id")

        if form_id:
            try:
                personal = KisanPersonalLandDetails.objects.get(form_id=form_id)
                plan = KisanPlanTechnicalBankDetails.objects.get(form_id=form_id)
                application = KisanApplicationDocuments.objects.get(form_id=form_id)
            except (KisanPersonalLandDetails.DoesNotExist, KisanPlanTechnicalBankDetails.DoesNotExist, KisanApplicationDocuments.DoesNotExist):
                return Response({"success": False, "message": "Application not found."}, status=status.HTTP_404_NOT_FOUND)

            return Response({
                "success": True,
                "form_id": form_id,
                "data": {
                    "personal": KisanPersonalLandDetailsSerializer(personal).data,
                    "plan_technical_bank": KisanPlanTechnicalBankDetailsSerializer(plan).data,
                    "application_documents": KisanApplicationDocumentsSerializer(application).data
                }
            }, status=status.HTTP_200_OK)

        personal_records = KisanPersonalLandDetails.objects.all().order_by("-id")
        result = []

        for personal in personal_records:
            form_id = personal.form_id
            plan = KisanPlanTechnicalBankDetails.objects.filter(form_id=form_id).first()
            application = KisanApplicationDocuments.objects.filter(form_id=form_id).first()

            result.append({
                "form_id": form_id,
                "personal": KisanPersonalLandDetailsSerializer(personal).data,
                "plan_technical_bank": KisanPlanTechnicalBankDetailsSerializer(plan).data if plan else None,
                "application_documents": KisanApplicationDocumentsSerializer(application).data if application else None
            })

        return Response({"success": True, "count": len(result), "data": result}, status=status.HTTP_200_OK)


class KisanPersonalLandDetailsUpdateAPIView(APIView):

    @transaction.atomic
    def put(self, request):
        form_id = request.data.get("form_id")

        if not form_id:
            return Response({"success": False, "message": "form_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            instance = KisanPersonalLandDetails.objects.get(form_id=form_id)
        except KisanPersonalLandDetails.DoesNotExist:
            return Response({"success": False, "message": "Personal land details not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = KisanPersonalLandDetailsSerializer(instance, data=request.data, partial=True)

        if not serializer.is_valid():
            return Response({"success": False, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return Response({"success": True, "message": "Personal and land details updated successfully.", "data": serializer.data}, status=status.HTTP_200_OK)


class KisanPlanTechnicalBankUpdateAPIView(APIView):

    @transaction.atomic
    def put(self, request):
        form_id = request.data.get("form_id")

        if not form_id:
            return Response({"success": False, "message": "form_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            instance = KisanPlanTechnicalBankDetails.objects.get(form_id=form_id)
        except KisanPlanTechnicalBankDetails.DoesNotExist:
            return Response({"success": False, "message": "Plan technical bank details not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = KisanPlanTechnicalBankDetailsSerializer(instance, data=request.data, partial=True)

        if not serializer.is_valid():
            return Response({"success": False, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return Response({"success": True, "message": "Plan, technical and bank details updated successfully.", "data": serializer.data}, status=status.HTTP_200_OK)


class KisanApplicationDocumentsUpdateAPIView(APIView):

    @transaction.atomic
    def put(self, request):
        form_id = request.data.get("form_id")

        if not form_id:
            return Response({"success": False, "message": "form_id is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            instance = KisanApplicationDocuments.objects.get(form_id=form_id)
        except KisanApplicationDocuments.DoesNotExist:
            return Response({"success": False, "message": "Application documents not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = KisanApplicationDocumentsSerializer(instance, data=request.data, partial=True)

        if not serializer.is_valid():
            return Response({"success": False, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return Response({"success": True, "message": "Application and documents updated successfully.", "data": serializer.data}, status=status.HTTP_200_OK) 
        
from .models import CenterLink,CenterLinkDetail
from .serializers import CenterLinkSerializer,CenterLinkDetailSerializer
        
class CenterLinkAPIView(APIView):

    # GET ALL
    def get(self, request):
        center_name = request.query_params.get("center_name")
    
        data = CenterLink.objects.all().order_by("-id")
    
        if center_name:
            data = [
                obj for obj in data
                if center_name in (obj.center_names or [])
            ]
    
        serializer = CenterLinkSerializer(data, many=True)
    
        return Response({
            "success": True,
            "message": "Data fetched successfully",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    # POST
    def post(self, request):
        serializer = CenterLinkSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()

            return Response({
                "success": True,
                "message": "Data created successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)

        return Response({
            "success": False,
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class CenterLinkDetailAPIView(APIView):

    # GET SINGLE
    def get(self, request, pk):
        try:
            obj = CenterLink.objects.get(pk=pk)
        except CenterLink.DoesNotExist:
            return Response({
                "success": False,
                "message": "Data not found"
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = CenterLinkSerializer(obj)

        return Response({
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    # PUT
    def put(self, request, pk):
        try:
            obj = CenterLink.objects.get(pk=pk)
        except CenterLink.DoesNotExist:
            return Response({
                "success": False,
                "message": "Data not found"
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = CenterLinkSerializer(
            obj,
            data=request.data
        )

        if serializer.is_valid():
            serializer.save()

            return Response({
                "success": True,
                "message": "Data updated successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        return Response({
            "success": False,
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    # DELETE
    def delete(self, request, pk):
        try:
            obj = CenterLink.objects.get(pk=pk)
        except CenterLink.DoesNotExist:
            return Response({
                "success": False,
                "message": "Data not found"
            }, status=status.HTTP_404_NOT_FOUND)

        obj.delete()

        return Response({
            "success": True,
            "message": "Data deleted successfully"
        }, status=status.HTTP_200_OK)


class CenterLinkDetailCenterAPIView(APIView):

    # GET SINGLE
    def get(self, request):
        center_name = request.query_params.get("center_name")
    
        details = CenterLinkDetail.objects.select_related(
            "center_link"
        ).order_by("-id")
    
        if center_name:
            details = details.filter(center_name=center_name)
    
        if not details.exists():
            return Response({
                "success": False,
                "message": "Data not found"
            }, status=status.HTTP_404_NOT_FOUND)
    
        detail_serializer = CenterLinkDetailSerializer(
            details,
            many=True
        )
    
        # Get unique CenterLinks
        center_links = CenterLink.objects.filter(
            details__in=details
        ).distinct()
    
        center_serializer = CenterLinkSerializer(
            center_links,
            many=True
        )
    
        return Response({
            "success": True,
            "center_link": center_serializer.data,
            "details": detail_serializer.data
        }, status=status.HTTP_200_OK)
    
        # POST
    def post(self, request):
            serializer = CenterLinkDetailSerializer(
                data=request.data
            )
    
            if serializer.is_valid():
                serializer.save()
    
                return Response({
                    "success": True,
                    "message": "Data created successfully",
                    "data": serializer.data
                }, status=status.HTTP_201_CREATED)
    
            return Response({
                "success": False,
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

    # PUT
    def put(self, request, pk):
        try:
            obj = CenterLinkDetail.objects.get(pk=pk)
        except CenterLinkDetail.DoesNotExist:
            return Response({
                "success": False,
                "message": "Data not found"
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = CenterLinkDetailSerializer(
            obj,
            data=request.data
        )

        if serializer.is_valid():
            serializer.save()

            return Response({
                "success": True,
                "message": "Data updated successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        return Response({
            "success": False,
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    # DELETE
    def delete(self, request, pk):
        try:
            obj = CenterLinkDetail.objects.get(pk=pk)
        except CenterLinkDetail.DoesNotExist:
            return Response({
                "success": False,
                "message": "Data not found"
            }, status=status.HTTP_404_NOT_FOUND)

        obj.delete()

        return Response({
            "success": True,
            "message": "Data deleted successfully"
        }, status=status.HTTP_200_OK)
        
        
from .models import SalaryAttendanceReport
from .serializers import SalaryAttendanceReportSerializer


class SalaryAttendanceReportAPIView(APIView):

    # =========================
    # GET ALL / FILTER
    # =========================
    def get(self, request):

        center_name = request.query_params.get("center_name")

        queryset = SalaryAttendanceReport.objects.all()

        if center_name:
            queryset = queryset.filter(center_name=center_name)

        serializer = SalaryAttendanceReportSerializer(
            queryset,
            many=True
        )

        return Response({
            "success": True,
            "count": queryset.count(),
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    # =========================
    # POST
    # =========================
    def post(self, request):

        serializer = SalaryAttendanceReportSerializer(
            data=request.data
        )

        if serializer.is_valid():
            serializer.save()

            return Response({
                "success": True,
                "message": "Salary attendance report created successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)

        return Response({
            "success": False,
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


class SalaryAttendanceReportDetailAPIView(APIView):

    # =========================
    # GET SINGLE
    # =========================
    def get(self, request, pk):

        try:
            obj = SalaryAttendanceReport.objects.get(pk=pk)
        except SalaryAttendanceReport.DoesNotExist:
            return Response({
                "success": False,
                "message": "Data not found"
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = SalaryAttendanceReportSerializer(obj)

        return Response({
            "success": True,
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    # =========================
    # PUT
    # =========================
    def put(self, request, pk):

        try:
            obj = SalaryAttendanceReport.objects.get(pk=pk)
        except SalaryAttendanceReport.DoesNotExist:
            return Response({
                "success": False,
                "message": "Data not found"
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = SalaryAttendanceReportSerializer(
            obj,
            data=request.data
        )

        if serializer.is_valid():
            serializer.save()

            return Response({
                "success": True,
                "message": "Data updated successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)

        return Response({
            "success": False,
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    # =========================
    # DELETE
    # =========================
    def delete(self, request, pk):

        try:
            obj = SalaryAttendanceReport.objects.get(pk=pk)
        except SalaryAttendanceReport.DoesNotExist:
            return Response({
                "success": False,
                "message": "Data not found"
            }, status=status.HTTP_404_NOT_FOUND)

        obj.delete()

        return Response({
            "success": True,
            "message": "Data deleted successfully"
        }, status=status.HTTP_200_OK)
        

from .models import MonthAttendanceReport
from .serializers import MonthAttendanceReportSerializer
class MonthAttendanceReportListAPIView(APIView):

    def get(self, request):

        center_name = request.query_params.get("center_name")

        reports = MonthAttendanceReport.objects.all().order_by(
            "-financial_year",
            "-month"
        )

        if center_name:
            reports = reports.filter(center_name=center_name)

        serializer = MonthAttendanceReportSerializer(
            reports,
            many=True
        )

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    def post(self, request):

        serializer = MonthAttendanceReportSerializer(
            data=request.data
        )

        if serializer.is_valid():
            serializer.save()

            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
import os

from django.http import JsonResponse, FileResponse
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


class MonthAttendanceReportDetailAPIView(APIView):

    def get_object(self, pk):

        try:
            return MonthAttendanceReport.objects.get(pk=pk)
        except MonthAttendanceReport.DoesNotExist:
            return None

    # GET EXCEL FILE
    def get(self, request, pk):

        report = self.get_object(pk)

        if not report:
            return JsonResponse(
                {"error": "Month attendance report not found."},
                status=404
            )

        if not report.month_attendance:
            return JsonResponse(
                {"error": "Excel file is not available for this report."},
                status=404
            )

        file_path = report.month_attendance.path

        if not os.path.exists(file_path):
            return JsonResponse(
                {
                    "error": "Excel file does not exist on the server.",
                    "path": file_path
                },
                status=404
            )

        response = FileResponse(
            open(file_path, "rb"),
            content_type=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            )
        )

        response["Content-Disposition"] = (
            f'inline; filename="{os.path.basename(file_path)}"'
        )

        response["Access-Control-Allow-Origin"] = "http://localhost:3000"

        return response

    # PUT
    def put(self, request, pk):

        report = self.get_object(pk)

        if not report:
            return Response(
                {"detail": "Month attendance report not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = MonthAttendanceReportSerializer(
            report,
            data=request.data
        )

        if serializer.is_valid():
            serializer.save()

            return Response(
                serializer.data,
                status=status.HTTP_200_OK
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    # DELETE
    def delete(self, request, pk):

        report = self.get_object(pk)

        if not report:
            return Response(
                {"detail": "Month attendance report not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        report.delete()

        return Response(
            {"message": "Month attendance report deleted successfully."},
            status=status.HTTP_204_NO_CONTENT
        )