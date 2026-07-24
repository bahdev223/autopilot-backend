from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect
from django_rh.models import Employee, Department, Position
from django_rh.services import EmployeeService


@login_required
def employes_liste(request):
    employes = Employee.objects.select_related("department", "position").all()
    return render(request, "rh/liste.html", {
        "employes": employes.order_by("last_name", "first_name"),
        "breadcrumbs": [{"label": "Employés"}],
    })


@login_required
def employe_creer(request):
    departments = Department.objects.all()
    positions = Position.objects.all()
    if request.method == "POST":
        try:
            svc = EmployeeService()
            emp = svc.create(
                first_name=request.POST["first_name"],
                last_name=request.POST["last_name"],
                sex=request.POST.get("sex", "M"),
                birth_date=request.POST.get("birth_date") or None,
                phone=request.POST.get("phone", ""),
                email=request.POST.get("email", ""),
                department_id=request.POST.get("department_id") or None,
                position_id=request.POST.get("position_id") or None,
                contract_type=request.POST.get("contract_type", "CDI"),
                created_by_id=request.user.id,
            )
            messages.success(request, f"Employé {emp.first_name} {emp.last_name} créé.")
            return redirect("employes_liste")
        except Exception as e:
            messages.error(request, str(e))
    return render(request, "rh/formulaire.html", {
        "departments": departments,
        "positions": positions,
        "mode": "creer",
        "breadcrumbs": [{"url": "/rh/", "label": "Employés"}, {"label": "Nouveau"}],
    })