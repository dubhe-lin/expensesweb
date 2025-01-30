from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Source, UserIncome
from django.core.paginator import Paginator
from userpreferences.models import UserPreference
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
import json
from django.http import JsonResponse

# Create your views here.

def search_income(request):
    if request.method=='POST':
        search_str=json.loads(request.body).get('searchText','')

        incomes=UserIncome.objects.filter(
            amount__startswith=search_str, owner=request.user) | UserIncome.objects.filter(
            date__startswith=search_str, owner=request.user) | UserIncome.objects.filter(
            description__icontains=search_str, owner=request.user) | UserIncome.objects.filter(
            source__icontains=search_str, owner=request.user) 
        
        data=incomes.values()
        return JsonResponse(list(data), safe=False)


@login_required(login_url='/authentication/login')
def index(request):
    sources = Source.objects.all()
    incomes= UserIncome.objects.filter(owner=request.user)
    paginator = Paginator(incomes, 3)

    page_number = request.GET.get('page')
    page_obj=paginator.get_page(page_number)
    try:
        currency = UserPreference.objects.get(user=request.user).currency
    except ObjectDoesNotExist:
        currency = "Default"
    context = {
        'incomes': incomes,
        'page_obj': page_obj,
        'currency': currency,
    }
    return render(request, 'income/index.html', context)

def add_income(request):
    sources = Source.objects.all()
    context = {
        'sources': sources,
        'values': request.POST,
    }
    if request.method == 'GET':
        return render(request, 'income/add_income.html', context)

    if request.method=='POST':
        amount = request.POST['amount']
        description = request.POST['description']
        date = request.POST['income_date']
        sources = request.POST['source']

        if not amount:
            messages.error(request, 'Amount is required')
            return render(request, 'income/add_income.html', context)
        

        if not description:
            messages.error(request, 'Description is required')
            return render(request, 'income/add_income.html', context)
        UserIncome.objects.create(owner=request.user, amount=amount, date=date, description=description, source=sources)
        messages.success(request, 'Record saved successfully')
        return redirect('income')

def edit_income (request, id):
    income=UserIncome.objects.get(pk=id)
    sources = Source.objects.all()
    context = {
        'income': income,
        'values': income,
        'sources': sources,
    }
    if request.method=='GET':
        return render(request, 'income/edit_income.html', context)
    if request.method=='POST':
        amount = request.POST['amount']
        description = request.POST['description']
        date = request.POST['income_date']
        source = request.POST['source']

        if not amount:
            messages.error(request, 'Amount is required')
            return render(request, 'income/edit_income.html', context)

        if not description:
            messages.error(request, 'Description is required')
            return render(request, 'income/edit_income.html', context)
                
        # income.owner=request.user
        income.amount=amount 
        income.date=date 
        income.description=description 
        income.source=source
        income.save()
        messages.success(request, 'Record updated successfully')
        return redirect('income')
    
    else: 
        messages.info(request, 'Handling post form')
    return render(request, 'income/edit_income.html', context)

def delete_income(request, id):
    income=UserIncome.objects.get(pk=id)
    income.delete()
    messages.success(request, 'Record removed')
    return redirect('income')