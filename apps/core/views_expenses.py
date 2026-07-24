from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q

from django_expenses.models import Expense, ExpenseCategory, CostCenter
from django_expenses.constants import ExpenseStatus, ExpenseNature
from django_expenses.services.expense_service import ExpenseService
from django_expenses.exceptions import WorkflowError
from django.core.exceptions import PermissionDenied


@login_required
def expenses_liste(request):
    etab = getattr(request, "etablissement_actif", None)
    qs = Expense.objects.select_related("user", "category", "cost_center")
    if etab:
        qs = qs.filter(user__adhesions_formation__etablissement=etab)
    q = request.GET.get("q", "")
    if q:
        qs = qs.filter(Q(description__icontains=q) | Q(reference_number__icontains=q) | Q(vendor__icontains=q))
    status = request.GET.get("status", "")
    if status:
        qs = qs.filter(status=status)
    stats = {
        "total": qs.count(),
        "brouillons": qs.filter(status=ExpenseStatus.DRAFT).count(),
        "soumises": qs.filter(status=ExpenseStatus.SUBMITTED).count(),
        "approuvees": qs.filter(status=ExpenseStatus.APPROVED).count(),
        "payees": qs.filter(status=ExpenseStatus.PAID).count(),
    }
    return render(request, "expenses/liste.html", {
        "expenses": qs.order_by("-created_at")[:50],
        "stats": stats,
        "q": q,
        "status": status,
        "status_choices": ExpenseStatus.CHOICES,
    })


@login_required
def expense_creer(request):
    if request.method == "POST":
        try:
            data = {
                "category_id": request.POST.get("category"),
                "expense_nature": request.POST.get("expense_nature", ""),
                "cost_center_id": request.POST.get("cost_center") or None,
                "amount": request.POST.get("amount", 0),
                "tax_amount": request.POST.get("tax_amount", 0),
                "currency": request.POST.get("currency", "XOF"),
                "description": request.POST.get("description", ""),
                "vendor": request.POST.get("vendor", ""),
                "date_incurred": request.POST.get("date_incurred"),
                "user": request.user,
            }
            expense = ExpenseService.create(data, user=request.user)
            messages.success(request, f"Dépense créée.")
            return redirect("expense_fiche", id=expense.id)
        except Exception as e:
            messages.error(request, str(e))
    categories = ExpenseCategory.objects.filter(is_active=True).order_by("code")
    cost_centers = CostCenter.objects.filter(is_active=True).order_by("code")
    return render(request, "expenses/formulaire.html", {
        "mode": "creer",
        "categories": categories,
        "cost_centers": cost_centers,
        "natures": ExpenseNature.CHOICES,
    })


@login_required
def expense_fiche(request, id):
    expense = get_object_or_404(
        Expense.objects.select_related("user", "category", "cost_center", "approved_by")
        .prefetch_related("attachments", "approvals__approved_by", "payments", "comments__user"),
        id=id,
    )
    return render(request, "expenses/fiche.html", {
        "expense": expense,
        "breadcrumbs": [
            {"url": "/depenses/", "label": "Dépenses"},
            {"label": expense.reference_number or f"Dépense #{expense.id}"},
        ],
    })


@login_required
def expense_modifier(request, id):
    expense = get_object_or_404(Expense, id=id)
    if request.method == "POST":
        try:
            data = {
                "category_id": request.POST.get("category"),
                "expense_nature": request.POST.get("expense_nature", ""),
                "cost_center_id": request.POST.get("cost_center") or None,
                "amount": request.POST.get("amount", 0),
                "tax_amount": request.POST.get("tax_amount", 0),
                "currency": request.POST.get("currency", "XOF"),
                "description": request.POST.get("description", ""),
                "vendor": request.POST.get("vendor", ""),
                "date_incurred": request.POST.get("date_incurred"),
            }
            ExpenseService.update(expense, data, user=request.user)
            messages.success(request, "Dépense mise à jour.")
            return redirect("expense_fiche", id=expense.id)
        except Exception as e:
            messages.error(request, str(e))
    categories = ExpenseCategory.objects.filter(is_active=True).order_by("code")
    cost_centers = CostCenter.objects.filter(is_active=True).order_by("code")
    return render(request, "expenses/formulaire.html", {
        "mode": "modifier",
        "expense": expense,
        "categories": categories,
        "cost_centers": cost_centers,
        "natures": ExpenseNature.CHOICES,
    })


@login_required
def expense_supprimer(request, id):
    expense = get_object_or_404(Expense, id=id)
    if request.method == "POST":
        try:
            expense.delete()
            messages.success(request, "Dépense supprimée.")
            return redirect("expenses_liste")
        except Exception as e:
            messages.error(request, str(e))
    return render(request, "expenses/confirmer_suppression.html", {
        "expense": expense,
    })


@login_required
def expense_soumettre(request, id):
    expense = get_object_or_404(Expense, id=id)
    if request.method == "POST":
        try:
            ExpenseService.submit(expense, user=request.user)
            messages.success(request, "Dépense soumise.")
        except (WorkflowError, PermissionDenied) as e:
            messages.error(request, str(e))
    return redirect("expense_fiche", id=expense.id)


@login_required
def expense_approuver(request, id):
    expense = get_object_or_404(Expense, id=id)
    if request.method == "POST":
        try:
            comment = request.POST.get("comment", "")
            ExpenseService.approve(expense, user=request.user, comment=comment)
            messages.success(request, "Dépense approuvée.")
        except (WorkflowError, PermissionDenied) as e:
            messages.error(request, str(e))
    return redirect("expense_fiche", id=expense.id)


@login_required
def expense_rejeter(request, id):
    expense = get_object_or_404(Expense, id=id)
    if request.method == "POST":
        try:
            reason = request.POST.get("reason", "")
            ExpenseService.reject(expense, user=request.user, reason=reason)
            messages.success(request, "Dépense rejetée.")
        except (WorkflowError, PermissionDenied) as e:
            messages.error(request, str(e))
    return redirect("expense_fiche", id=expense.id)


@login_required
def expense_payer(request, id):
    expense = get_object_or_404(Expense, id=id)
    if request.method == "POST":
        try:
            payment_data = {
                "payment_method": request.POST.get("payment_method", ""),
                "amount_paid": request.POST.get("amount_paid", expense.total_amount),
                "reference": request.POST.get("reference", ""),
                "notes": request.POST.get("notes", ""),
            }
            ExpenseService.pay(expense, user=request.user, payment_data=payment_data)
            messages.success(request, "Paiement enregistré.")
        except (WorkflowError, PermissionDenied) as e:
            messages.error(request, str(e))
    return redirect("expense_fiche", id=expense.id)


@login_required
def expense_annuler(request, id):
    expense = get_object_or_404(Expense, id=id)
    if request.method == "POST":
        try:
            ExpenseService.cancel(expense, user=request.user)
            messages.success(request, "Dépense annulée.")
        except (WorkflowError, PermissionDenied) as e:
            messages.error(request, str(e))
    return redirect("expense_fiche", id=expense.id)
