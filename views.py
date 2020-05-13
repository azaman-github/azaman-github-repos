#
# import module that deals with Cros Site Request Fraudgery
#
from django.views.decorators.csrf import csrf_exempt
#
# import django model for user and module to authenticate  user
#
from django.contrib.auth.models import User
from django.contrib.auth        import authenticate
#
# import models
#
from library.models import Person 
from library.models import Book 
from library.models import BookInstance
from library.models import BooksOnLoan
from library.models import Logon
from library.models import BooksOnReservationList
#
#import forms
#
from library.forms import LoginForm
from library.forms import NewAccountForm
from library.forms import BookLoanForm
from library.forms import BookReturnForm
from library.forms import BooksOnReservationListForm
# 
from django.core.mail import send_mail
from django.core      import mail
from  django.conf     import  settings as  s
import imaplib
import re
import time
#
# import python modules
#
from  datetime  import date
import datetime
import time
import  sys
#
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
def index(request):  
    context={}
    return render(request,'index.html', context )   
#
##++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Name      :check_for_login 
# Overview  :The function checks cookies to establish whhether the person is already logged on.
# Notes     :
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
def  check_for_login (request) :
    global  ret_obj
    if request.session.has_key('username'):
          template = loader.get_template('already_logged_in.html')
          ret_obj=HttpResponse(template.render())
          return True
    else:
          return False
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Name     : process_post_for_login
# Overview : The function is used to process POST method for login
#
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
def process_post_for_login (request) :
    #
    form=LoginForm(request.POST )
    #
    email=""
    password=""
    if form.is_valid() :
         email= (form.cleaned_data.get("email")).strip()
         password  = (form.cleaned_data.get("password")).strip()
    else :
         context ={'server_error': "Invalid data entered in the form" }
         return render (request,'server_error.html', context)
    #
    context = { 'email': email, 'password': password }
    #
    # authenticate  user using authenticate ()
    #
    try :
           user=authenticate(username=email, password = password )
           if user is  None  : 
                 context ={'server_error': "Invalid email id or password" }
                 return render (request,'server_error.html', context)
    except  Exception as  e :
                 context ={'server_error': str(e) }
                 return render (request,'server_error.html', context)
    try :
        #
        # record the login for this  user
        #
        lObj = Logon( email=email, login_dt=datetime.datetime.now(),logout_dt=None)
        lObj.save()
        #
        # update logout_dt for any user where logout date wasn't captured
        #
        Logon.objects.filter(logout_dt__isnull=True).exclude(email__iexact=email).update(logout_dt=datetime.datetime.now() )
    except Exception as  e  :
            context ={ 'server_error': str(e) }
            return render (request,'server_error.html', context)
    #
    # user has logged in
    # create a session to control user navigations
    #
    request.session['username'] = "zaman"
    request.session['email']    = email
    #response.set_cookie['username'] = "azaman"
    #
    response = render(request, 'login_ok.html')
    return render (request,"login_ok.html",{} )
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Name     : process_get_for_login 
# Overview : The function is used to process GET method for login
# Notes    :
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
def process_get_for_login (request) :
        form = LoginForm()
        context = { 'form': form }
        return render (request,'registration/login.html',{'form' : form} )
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
@csrf_exempt
def login(request):
    #
    if request.method == 'POST':
             return ( process_post_for_login (request) )
    else :
         #
         # check cookies to establish whether or not the user is alreday logged on
         #
         return ( process_get_for_login (request))

#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Name      : logged_on
# Overview  : The function is used to display the the main menu without the login tab
# Notes    :
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
def logged_on(request) :
        context={}
        return render(request,'index_without_login.html', context)
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
def validate_email(request,email) :
   #
   # send email to address to be validated
   #
   subject="Test Mail"
   msg   = "Test Mail"
   rc , rm = send_email  (request,email,subject,msg)
   if not (rc ) :
       return rc, rm 
   #
   # allow sometime for bounced email to be recieved
   #
   time.sleep(5)
   #
   # check for Undeliverable messages with target email id
   #
   imap_host ="imap-mail.outlook.com"
   imap_user ="Arif.Zaman@hotmail.co.uk"
   imap_pass ="namaZ!!!*@firA!"
   #
   try :
         # connect to host using SSL
         #
         imap = imaplib.IMAP4_SSL(imap_host)
         #
         # login to server
         #
         imap.login(imap_user, imap_pass)
         imap.select('Inbox')
         #
         # lomn=['1000 2340 4566 6666 '] # string of message numbers separated by space , stored in a list
         #
         rc,lomn  = imap.search(None,'(SUBJECT "Undeliverable:")')
         #
         if  rc != "OK" :
             #
             # no messages found; email vetified
             #
             msg="Email verified"
             return True,  msg
         # 
         for msg_no in lomn[0].split():
               rc, data = imap.fetch(msg_no, '(RFC822)')
               '''
               data       = [ (te1, te2) ]  # list of tuples
               data[0]    = first element of list
               data[0][0] = first element of tuple within list
               data[0][1] = second element of tuple within list
               '''
               s=str(data[0][1])
               match=re.search(email, s)
               if ( match == None ) :
                    continue
               if (str(match)).find("Arif.Zaman@hotmail.co.uk") > 0 :
                   msg="Email Verified"
                   return True,msg 
               else :
                   #
                   # target email bounced
                   #
                   msg="Invalid Email"
                   return False,msg 
         imap.close()
         #
         # no Undeliverable message for the target email received
         #
         msg="Email verified"
         return True,  msg
         #
   except Exception  as  e :
         err_msg = str(e)
         msg ="Failed to verify email address because " + err_msg
         return False , msg
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Name      : process_post_for_account
# Overview  : The function is used to process POST method for account creation
# Notes    :
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
def process_post_for_account (request) :
        global ret_obj
        #
        #getting values from post
        #
        form=NewAccountForm(request.POST or None)
        #
        if form.is_valid() :
            fname= form.cleaned_data.get("fname")
            lname= form.cleaned_data.get("lname")
            dob  = form.cleaned_data.get("dob")
            email= (form.cleaned_data.get("email")).strip()
            pwd  = (form.cleaned_data.get("pwd")).strip()
        else:
            context ={'server_error': "Invalid data entered in the form" }
            return render (request,'server_error.html', context)
        #
        rc, msg=validate_email(request,email) 
        if not (rc ) :
            context ={'server_error': msg}
            return render (request,'server_error.html', context)
        #
        context = {'fname':fname,'lname':lname,'dob':dob,'email':email,'pwd':pwd }
        try :
           #
           # create an account for this user in django's authetication scheme
           #
           # username, email, password
           #
           user = User.objects.create_user( email,   email, pwd)
           user.save()
           # Update fields and then save again
           user.first_name = fname
           user.last_name  = lname
           user.save()
           #
        except Exception as  e : 
                if ( str(e).find('ORA-00001' ) >=  0 ) :
                     # unique contraint violation,; user already exists
                     erm= "ERROR:An account for user, " + email + " already exists; please logon"
                     context = { 'server_error': erm }
                else:
                     context = { 'server_error': str(e) }
                return render (request,'server_error.html', context)
        try  :
           #
           # create this user for the application
           #
           pObj = Person( fname=fname, lname=lname, dob=dob, email=email, pwd=pwd )
           pObj.save()
           #
           # record  this as login 
           # 
           lObj = Logon( email=email, login_dt=datetime.datetime.now(),logout_dt=None)
           lObj.save()
           #
           # update logout_dt for any user where logout date wasn't captured
           #
           Logon.objects.filter(logout_dt__isnull=True).exclude(email__iexact=email).update(logout_dt=datetime.datetime.now() )
           #
           # user should be in logged on state
           # create a session to control user navigations
           #
           request.session['username'] = "zaman"
           request.session['email']    = email
           #
           context = {'fname':fname,'lname':lname,'dob':dob,'email':email }
           return render ( request,'new_acct_ok.html', context)
           #
        except Exception as  e  :
               context = { 'server_error': str(e) }
               return render (request,'server_error.html', context)
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Name      : process_get_for_account
# Overview  : The function is used to process get method for account creation
# Notes    :
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
def process_get_for_account (request) :
        global ret_obj
        #
        form = NewAccountForm()
        context = { 'form': form }
        return render(request,'new_account_form.html', context)
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
@csrf_exempt
def create_new_account(request):
    global ret_obj
    #
    # check cookies to establish whether or not the user is alreday logged on
    #
    if  check_for_login (request)  :
              return ret_obj
    #
    # process request method
    #
    if request.method == 'POST':
         return ( process_post_for_account (request)) 
    else:
         return (process_get_for_account (request))
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++o
def  listBooks ( request ):
     if not ( check_for_login (request )) :
          template = loader.get_template('not_logged_in.html')
          return HttpResponse(template.render(None , request))
     #
     all_books = Book.objects.all()
     context ={'all_books' : all_books }
     template = loader.get_template('list_books.html')
     return HttpResponse(template.render(context,request))
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
from django.views.generic.list  import ListView
#
class BookListView(ListView):
    model = Book
    #template_name = '/home/azaman/django/.venv1/proto/library/templates/book_list.html'  

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        template = loader.get_template('/home/azaman/django/.venv1/proto/library/templates/book_list.html')  
        return HttpResponse(template.render(context,None))
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
def check_isbn_stock_availability (isbn, request):
    '''
    Check to see if this book is in the collection
    '''
    context={}
    qs= BookInstance.objects.all().filter(isbn = isbn ).values ('id','status')
    if ( len(qs) == 0  ) :
         return False
    else: 
         return qs

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
def  check_isbn_already_loan (isbn, email, request) :
      '''
       check to see if this book is already on loan to this person
      '''
      context={}
      #
      bol_qs= BooksOnLoan.objects.all().filter(isbn_id = isbn , email_id = email ,returned_on= None ).values ()
      if  (bol_qs.count() > 0  )  :
          return False 
      else:
           return True
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
def  loan_book (request, qs, email, isbn) :
    '''
    Loan this book, if any instance is available for loan
    ''' 
    today_plus_7=date.today() + datetime.timedelta(days=7)
    context={}
    #
    # retrieve book title
    #
    book_title=Book.objects.all().filter(isbn = isbn).values('title')
    # 
    for rec_dict  in qs:
        for  k, v in rec_dict.items() :
            if ( k == 'status' and v  == "a")  :
                bolObj = BooksOnLoan (book_title=book_title ,isbn_id=isbn, bi_id=rec_dict['id'],email_id = email,
                                                         loaned_on=date.today(),due_back=today_plus_7  )
                bolObj.save()
                #
                # update bookinstance  for  this  copy of the book
                #
                BookInstance.objects.filter(id=rec_dict['id']).update(status='o')
                #
                # any more instances available for this book ?
                #
                qs1=BookInstance.objects.filter(isbn=isbn, status='a')
                if (len (qs1)  == 0 ) :
                     #
                     # no instance of this book is available for loan
                     # set Book.available_for_loan to N for this isbn
                     #
                     Book.objects.filter(isbn=isbn).update(available_for_loan='N')
                     #
                return True, book_title, today_plus_7 
        else :
                #
                # no instance of this book is available for loan
                #
                return False,  book_title, today_plus_7 
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
def send_email  (request,email,subject,msg):
    '''
    1. send_mail() needs to know the definition of ENAME_BACKEND wgich can defined in settings.py file or via the environment variabe

    2. settings.py file has the default definition for this  as  follows:
       ENAME_BACKEND='django.core.mail.backends.smtp.EmailBackend'

    3. To be able to send email using django's email facility outside the application,
       set following enviromment variables as follows:
       export PYTHONPATH="${PYTHONPATH}:/home/azaman/django/.venv1/proto/ptoto/"
       export DJANGO_SETTINGS_MODULE="settings"

    4. These two variables enable django to located settings.py file and read the EMAIL_BACKEND definition.
     
    '''
    #
    email_host="smtp.live.com"
    email_port=25
    email_host_user="Arif.Zaman@hotmail.co.uk"
    email_host_password="namaZ!!!*@firA!" 
    email_use_tls=True
    from_email="Arif.Zaman@hotmail.co.uk"
    #
    #msg=""
    try  :
           connection=mail.get_connection(host=email_host,port=email_port,username=email_host_user,use_tls=email_use_tls,password=email_host_password )
           send_mail (subject=subject, message=msg, from_email=from_email,recipient_list=[email], connection=connection)
           msg="Successfully sent email"
           return True,  msg
    except Exception  as  e  :
           err_msg=str(e)
           msg="Failed to send email because " + err_msg 
           return False, msg
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
def process_post_for_borrow_books(request):
        # 
        form=BookLoanForm(request.POST or None)
        #
        context={}
        if not form.is_valid() :
             return render (request,'invalid_isbn', context)
        #
        isbn= (form.cleaned_data.get("isbn")).strip()
        if not isbn.isdecimal() :
             return render (request,'invalid_isbn', context)
        #
        #
        try :
             email_id = request.session['email']
             #
             if  not ( check_isbn_stock_availability (isbn, request) ):
                    return render(request,'book_instance_not_available',context)
             qs=check_isbn_stock_availability (isbn, request) 
             #
             if not ( check_isbn_already_loan (isbn, email_id,request) ):
                 return render (request,'book_on_loan_to_you.html', context)
             #
             #
             success,book_title,today_plus_7=loan_book(request, qs, email_id, isbn) 
             if not (success ) :
                   #
                   # no instance of this book is available for loan
                   # set Book.available_for_loan to N for this isbn
                   #
                   Book.objects.filter(isbn=isbn).update(available_for_loan='N')
                   #
                   return  render(request,'book_not_available_for_loan.html',context)
             #
             req_format ="%-dth of %b, %Y"
             #
             today=date.today()
             today_str=today.strftime(req_format)
             #
             today_plus_7_str=today_plus_7.strftime(req_format)
             #
             msg=f"""Dear Sir/Madam,

You have borrowed a book entitled "{book_title[0]['title']}" on {today_str }
The book is due for return on {today_plus_7_str}

Yours truely,
Library Adminstrator """
             #
             send_email  (request,email=email_id,subject="Borrowed Book",  msg=msg)
             #
             return render (request,'loaned_book.html',context)
             #
        except Exception as  e :
               context =       { 'server_error': e }
               return render (request,'server_error.html',context)
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
def process_get_for_borrows_books  (request):
        #
        form = BookLoanForm()
        context = { 'form': form }
        #
        return render (request,'book_loan_form.html', context )
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
@csrf_exempt
def borrow_books(request):
    #
    global ret_obj
    #
    if not ( check_for_login (request )) :
          template = loader.get_template('not_logged_in.html')
          return HttpResponse(template.render(None , request))
    #
    # process request method
    #
    if request.method == 'POST':
         return ( process_post_for_borrow_books(request)) 
    else:
         return (process_get_for_borrows_books  (request))
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
def process_post_for_return_books  (request):
      try :
           # 
           #retrieve unique bookonloan id (id from BooksOnLoan ( it is captured from the drop down list in the form )
           #
           form=BookReturnForm(request.POST or None)
           #
           if form.is_valid() :
               id = form.cleaned_data.get("id")
           else:
               return render(request,'invalid_data.html',context) 
           # 
           # update booksonloan for this id
           #
           BooksOnLoan.objects.filter(id=id).update(returned_on=date.today())
           #
           # retrieve bi_id and isbn_id for  this  booksonloan,id
           # this return list an object
           #
           bol_rec=BooksOnLoan.objects.get(id=id)
           #
           # returns single object
           #
           bi_id   = bol_rec.bi_id
           isbn_id = bol_rec.isbn_id
           #
           # a book instance is returned
           # is this on reservationn list ?
           #
           reserved_books=BooksOnReservationList.objects.filter(isbn_id=isbn_id,book_available_dt__isnull=True ,
                                              book_borrowed_dt__isnull=True,reservation_cancelled='N').order_by ('reservation_dt')
           if ( len(reserved_books) > 0 ):
               #
               # update the  earliest reservation
               #
               earliest_reservation_rec=reserved_books[0]
               earliest_reservation_rec.book_available_dt=date.today()
               earliest_reservation_rec.save()
               email=earliest_reservation_rec.email_id
               #
               # update book instance
               #
               rec=BookInstance.objects.get(id=bi_id)
               rec.status='r'
               rec.save ()
               #
               # update Book 
               # set book_available_for_loan to N
               #
               rec=Book.objects.get(isbn=isbn_id)
               rec.available_for_loan='N'
               rec.save()
               #
               # send notification email to reservation owner
               #
               today_plus_7=str(date.today() + datetime.timedelta(days=7))
               msg=f"""Dear Sir/Madam,

Your reserved book "{rec.title}" is now available.
We will hold the book unti {today_plus_7}. 

Yours truely,
Library Adminstrator """
               subject="Reserved Book Available"
               send_email  (request,email,subject,msg)
               #
           else :
               #
               # update bookinstance
               #
               rec=BookInstance.objects.get(id=bi_id)
               rec.status='a'
               rec.save ()
               #
               # update Book 
               # set book_available_for_loan to Y
               #
               Book.objects.filter(isbn=isbn_id).update(available_for_loan='Y')
           context={}
           return render(request,'book_returned.html',context)
           #
      except Exception as  e  :
           err_msg = str(e)
           msg="Failed to process return for the book(BooksOLoan.Id=" + str(id) + ") because " + err_msg
           context = {'server_error': msg}
           return render(request,'server_error.html',context)
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
def process_get_for_return_books  (request):
        #
        #
        # retrieve email for session
        #
        email_id = (request.session['email']).strip()
        #
        # retrieve books for which all copies are currently on loans
        #
        #c=BookInstance.objects.filter(availble___exact='email_id).exclude(returned_on__isnull=False).count()
        #
        abtr=BooksOnLoan.objects.filter(email_id__exact=email_id).exclude(returned_on__isnull=False)
        if  (len(abtr)  == 0  )  :
            template = loader.get_template('no_book_due_back.html')
            return HttpResponse(template.render({},request))
        #
        # there are books to be returned
        #
        form = BookReturnForm(email=email_id)
        #
        context = {'form': form  }
        return render (request,'book_return_form.html',context)

#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
@csrf_exempt
def return_books(request):
    #
    global ret_obj
    #
    context={}
    if not ( check_for_login (request )) :
          return render(request,'not_logged_in.html', context)
    #
    # process request method
    #
    if request.method == 'POST':
         return ( process_post_for_return_books(request)) 
    else:
         return (process_get_for_return_books  (request))

#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
def process_post_for_reserve_books (request) :
    # 
    #retrieve unique isbn for Book, captured from the drop down list in the form 
    #
    form=BooksOnReservationListForm(request.POST or None)
    #
    if form.is_valid() :
          isbn = form.cleaned_data.get("isbn")
    else:
          return render(request,'invalid_data.html',context) 
    # 
    email_id=request.session['email']
    #
    # check to see if the book is currently in reservation list
    #
    Obj=BooksOnReservationList.objects.filter(isbn_id=isbn,email_id=email_id,book_available_dt=None)
    if ( len(Obj) > 0 )  :
          context={}
          return render (request,'book_already_on_reservation_list.html',context)
    #
    # create a record in BookOnReservationList for this id
    #
    person_rec=Person.objects.get(email__exact=email_id)
    book_rec=Book.objects.get(isbn__exact=isbn)
    #
    context={}
    Obj=BooksOnReservationList(email_id=person_rec.email,isbn_id=book_rec.isbn,title=book_rec.title,reservation_dt=date.today(),book_available_dt=None)
    #Obj=BooksOnReservationList(title=book_rec.title,reservation_dt=date.today(),book_available_dt=None)
    Obj.save ()
    #
    req_format ="%-dth of %b, %Y"
    today=date.today()
    today_str=today.strftime(req_format)
    #
    msg=f"""Dear Sir/Madam,
You have reserved the book entitled "{book_rec.title}" on {today_str }
You will be notified once the book is available for loan

Yours truely,
Library Adminstrator """
    #
    try :
          send_email  (request,email=email_id,subject="Reserved Book",  msg=msg)
          #
          return render(request,'book_reserved.html',context)
          #
    except Exception as  e :
               context =       { 'server_error': e }
               return render (request,'server_error.html',context)
  
#+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
def process_get_for_reserve_books (request) :
      qs=Book.objects.filter(available_for_loan__exact ='N' )
      context={}
      if ( len(qs)  == 0 ) :
         return render(request,'all_books_available.html',context)
      #
      form = BooksOnReservationListForm(email_id="", action="RB")
      # form = BooksOnReservationList( {'email_id':person_rec.email, 'action':"BRB"})
      #
      context = {'form': form  }
      return render(request,'book_reservation_form.html',context)
           
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
@csrf_exempt
def reserve_books(request):
    #
    if not ( check_for_login (request )) :
          template = loader.get_template('not_logged_in.html')
          return HttpResponse(template.render(None , request))
    #
    # process request method
    #
    if request.method == 'POST':
         return ( process_post_for_reserve_books(request)) 
    else:
         return (process_get_for_reserve_books  (request))
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
@csrf_exempt
def  process_post_for_borrow_reserved_books(request) :
    # 
    #retrieve unique isbn for Book, captured from the drop down list in the form 
    #
    form=BooksOnReservationListForm(request.POST or None)
    #
    if form.is_valid() :
          id    = form.cleaned_data.get("id")
          #title = form.cleaned_data.get("title")
    else:
          return render(request,'invalid_data.html',context) 
    # 
    # update reservation
    #
    rec=BooksOnReservationList.objects.get(id=id)
    rec.book_borrowed_dt=data.today ()
    isbn = rec.isbn_id
    #
    # update book instance
    #
    rec=BookInstance.objects.get(isbn=isbn_id, status='r')
    rec.statust='o'
    rec.save()
    #
    # send email
    #
    req_format ="%-dth of %b, %Y"
    #
    today=date.today()
    today_str=today.strftime(req_format)
    #
    today_plus_7_str=today_plus_7.strftime(req_format)
    #
    msg=f"""Dear Sir/Madam,

You have borrowed a book entitled "{title}" on {today_str }
The book is due for return on {today_plus_7_str}.
Reserved book incurs penalty(50p/day), if retured after due date.

Yours truely,
Library Adminstrator """
             #
    context={}
    template_msg ="All Done"
    context={'template_msg': template_msg}
    return render ( request,'display_message.html', context)
    #
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
@csrf_exempt
def process_get_for_borrow_reserved_books  (request):
     #
     # check to see if any reserved books are now available to borrow for this user
     #
     email=request.session['email']
     person_rec=Person.objects.get(email=email)
     #
     qs=BooksOnReservationList.objects.filter(email_id=person_rec.email,book_available_dt__isnull=False, book_borrowed_dt__isnull=True,reservation_cancelled='N' )
     #qs=BooksOnReservationList.objects.filter(book_available_dt__isnull=False, book_borrowed_dt__isnull=True,reservation_cancelled='N' )
     if ( len(qs) == 0 ) :
        template_msg ="You have no reserved books available to borrow at the moment"
        context={'template_msg': template_msg}
        return render ( request,'display_message.html', context)
     #
     form  = BooksOnReservationListForm(email_id=email, action="BRB")
     #form = BooksOnReservationList( {'email_id':person_rec.email, 'action':"BRB"})
     #form = BooksOnReservationList(email_id=person_rec.email)
     #
     context = {'form': form  }
     #context = { }
     return render (request,'borrow_reserved_book.html',context)
     #return render (request,'index.html',context)

#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
@csrf_exempt
def borrow_reserved_books( request ):
    if not ( check_for_login (request )) :
          context={}
          return render(request,'not_logged_in.html', context)
    #
    # process request method
    #
    if request.method == 'POST':
         return ( process_post_for_borrow_reserved_books(request)) 
    else:
         return (process_get_for_borrow_reserved_books  (request))
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
@csrf_exempt
def pay_fine (request):
      template_msg ="Functionality is under development"
      context={'template_msg': template_msg}
      return render ( request,'display_message.html', context)
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
# Name     : logout
# Overview : The function is used to process logout 
# Notes    : 
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
@csrf_exempt
def logout(request):
   if not ( check_for_login (request )) :
          template = loader.get_template('not_logged_in.html')
          return HttpResponse(template.render(None , request))
   try:
      email_id=request.session['email']
      Logon.objects.filter(email__iexact=email_id).update(logout_dt=datetime.datetime.now() )
      #
      context={}
      del request.session['username']
      del request.session['email']
      request.session.flush () 
      #return HttpResponse("<strong>You are logged out.</strong>")
      return render (request,'logout_form.html', context)
   except Exception as  e  :
      context ={ 'server_error': str(e) }
      template = loader.get_template('server_error.html')
      return HttpResponse(template.render(context, request))
      
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
