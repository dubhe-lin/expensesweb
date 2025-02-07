from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Category, Expense
from django.contrib import messages
from django.core.paginator import Paginator
import json
from django.http import JsonResponse, HttpResponse
from userpreferences.models import UserPreference
from django.core.exceptions import ObjectDoesNotExist
import datetime
import csv
import xlwt

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from io import BytesIO
import tempfile
from django.db.models import Sum
# from django.template.loader import render_to_string
# from weasyprint import HTML

# Create your views here.

def search_expenses(request):
    if request.method=='POST':
        search_str=json.loads(request.body).get('searchText','')

        expenses=Expense.objects.filter(
            amount__startswith=search_str, owner=request.user) | Expense.objects.filter(
            date__startswith=search_str, owner=request.user) | Expense.objects.filter(
            description__icontains=search_str, owner=request.user) | Expense.objects.filter(
            category__icontains=search_str, owner=request.user) 
        
        data=expenses.values()
        return JsonResponse(list(data), safe=False)
        

@login_required(login_url='/authentication/login')
def index(request):
    categories = Category.objects.all()
    expenses=Expense.objects.filter(owner=request.user)
    paginator = Paginator(expenses, 3)
    page_number = request.GET.get('page')
    page_obj=paginator.get_page(page_number)
    try:
        currency = UserPreference.objects.get(user=request.user).currency
    except ObjectDoesNotExist:
        currency = "Default"
    context = {
        'expenses': expenses,
        'page_obj': page_obj,
        'currency': currency,
    }
    return render(request, 'expenses/index.html', context)

def add_expense(request):
    categories = Category.objects.all()
    context = {
        'categories': categories,
        'values': request.POST,
    }
    if request.method == 'GET':
        return render(request, 'expenses/add_expense.html', context)

    if request.method=='POST':
        amount = request.POST['amount']
        description = request.POST['description']
        date = request.POST['date']
        categories = request.POST['category']

        if not amount:
            messages.error(request, 'Amount is required')
            return render(request, 'expenses/add_expense.html', context)
        

        if not description:
            messages.error(request, 'Description is required')
            return render(request, 'expenses/add_expense.html', context)
        Expense.objects.create(owner=request.user, amount=amount, date=date, description=description, category=categories)
        messages.success(request, 'Expense saved successfully')
        return redirect('expenses')

def edit_expense (request, id):
    expense=Expense.objects.get(pk=id)
    categories = Category.objects.all()
    context = {
        'expense': expense,
        'values': expense,
        'categories': categories,
    }
    if request.method=='GET':
        return render(request, 'expenses/edit_expense.html', context)
    if request.method=='POST':
        amount = request.POST['amount']
        description = request.POST['description']
        date = request.POST['date']
        category = request.POST['category']

        if not amount:
            messages.error(request, 'Amount is required')
            return render(request, 'expenses/edit_expense.html', context)

        if not description:
            messages.error(request, 'Description is required')
            return render(request, 'expenses/edit_expense.html', context)
                
        expense.owner=request.user
        expense.amount=amount 
        expense.date=date 
        expense.description=description 
        expense.category=category
        expense.save()
        messages.success(request, 'Expense updated successfully')
        return redirect('expenses')
    
    else: 
        messages.info(request, 'Handling post form')
    return render(request, 'expenses/edit_expense.html', context)

def delete_expense(request, id):
    expense=Expense.objects.get(pk=id)
    expense.delete()
    messages.success(request, 'Expense removed')
    return redirect('expenses')

def expense_category_summary(request):
    todays_date = datetime.date.today()
    six_months_ago=todays_date-datetime.timedelta(days=30*6)
    expenses=Expense.objects.filter(owner=request.user, date__gte=six_months_ago, date__lte=todays_date)
    finalrep={}

    def get_category(expense):
        return expense.category
    category_list = list(set(map(get_category, expenses)))

    def get_expense_category_amount(category):
        amount=0
        filtered_by_category=expenses.filter(category=category)

        for item in filtered_by_category:
            amount+=item.amount
        return amount
    
    for x in expenses:
        for y in category_list:
            finalrep[y]=get_expense_category_amount(y)
    
    return JsonResponse({'expense_category_data': finalrep}, safe=False
                        )
def stats_view(request):
    return render(request, 'expenses/stats.html') 

def export_csv(request):
    response=HttpResponse(content_type='text/csv')
    response['Content-Disposition']='attachment; filename=Expenses' + \
        str(datetime.datetime.now())+ '.csv'
    
    writer=csv.writer(response)
    writer.writerow(['Amount', 'Description', 'Category', 'Date'])

    expenses=Expense.objects.filter(owner=request.user)

    for expense in expenses:
        writer.writerow([expense.amount,expense.description, expense.category, expense.date])

    return response

def export_excel(request):
    response=HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename=Expenses' +\
        str(datetime.datetime.now())+'.xls'
    wb=xlwt.Workbook(encoding='utf-8')
    ws=wb.add_sheet('Expenses')
    row_num = 0
    font_style=xlwt.XFStyle()
    font_style.font.bold=True

    columns=['Amount', 'Description', 'Category', 'Date']
    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)
    font_style = xlwt.XFStyle()

    rows=Expense.objects.filter(owner=request.user).values_list('amount', 'description', 'category','date')

    for row in rows:
        row_num +=1

        for col_num in range(len(row)):
            ws.write(row_num,col_num,str(row[col_num]), font_style)
    
    wb.save(response)
    return response

def export_pdf(request):
    response=HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; attachment; filename=Expenses' + \
        str(datetime.datetime.now())+'.pdf'
    
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.setTitle("Expenses Report")

    expenses= Expense.objects.filter(owner=request.user)
    sum = expenses.aggregate(Sum('amount'))
    total = sum['amount__sum']

    #Set font for the company name
    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawCentredString(4.25 * inch, 10.5*inch, "TRULY EXPENSE MANAGEMENT")

    #Add title
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(100, 700, "Expenses Report")
    pdf.setFont("Helvetica", 10)

    # Table header
    pdf.drawString(100, 680, "Amount")
    pdf.drawString(200, 680, "Description")
    pdf.drawString(300, 680, "Category")
    pdf.drawString(400, 680, "Date")

    y = 660
    for expense in expenses:
        pdf.drawString(100, y, str(expense.amount))
        pdf.drawString(200, y, expense.description)
        pdf.drawString(300, y, expense.category)
        pdf.drawString(400, y, str(expense.date))
        y -= 20
        if y < 50:
            pdf.showPage()
            pdf.setFont("Helvetica", 10)
            y = 750
    

    
    pdf.drawString(100, y-10, 'Total: ' + str(total))

    pdf.save()
    buffer.seek(0)
    response.write(buffer.read())
    return response

# def export_pdf(request):
#     response=HttpResponse(content_type='application/pdf')
#     response['Content-Disposition'] = 'attachment; filename=Expenses' + \
#         str(datetime.datetime.now())+'.pdf'
#     response['Content-Transfer-Encoding']='binary'

#     html_string=render_to_string('expenses/pdf-output.html',{'expenses':[],'total':0})
#     html=HTML(string=html_string)
#     result = html.write_pdf()

#     with tempfile.NamedTemporaryFile(delete=True) as output:
#         output.write(result)
#         output.flush()

#         output=open(output.name, 'rb')
#         response.write(output.read())

#     return response