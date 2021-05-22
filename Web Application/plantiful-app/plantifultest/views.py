from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect
from django.core import serializers
from django.forms.models import formset_factory, model_to_dict, modelformset_factory
from .models import *
from django.contrib import messages
from django.urls import reverse_lazy,reverse
from passlib.hash import pbkdf2_sha256
from plotly.offline import plot
import plotly.graph_objs as go
from plotly.graph_objs import Scatter
import datetime
from .token import token_generator
from .token import sendInvitation
from .controller import *
from .forms import *
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.template.loader import render_to_string


# This function loads the register page and processes client's requests to register
def register(request):
    
    if (request.method == "POST"):
        first_name = request.POST["first_name"]
        last_name = request.POST["last_name"]
        email = request.POST["email"]
        pwd = request.POST["pwd"]
        rpwd = request.POST["rpwd"]
        security_token = request.POST["security_token"]

        #check if user exists
        try:
            obj = users.objects.get(email=email)
        except users.DoesNotExist:
           
            #if user does not exist, then check if they have a token
            try:
                usr_token = user_token.objects.get(invited_email=email)
                token = getattr(usr_token, 'token')
                
                if(security_token != token):
                    messages.error(request, 'Invalid Token.')
                    return HttpResponseRedirect(reverse_lazy('register'))
                
                dt = getattr(usr_token, 'created_at').date()
                dt_now = datetime.date.today()
                diff = abs((dt_now - dt).days)
                
                if(diff > 7):
                    messages.error(request, 'Token has expired.')
                    return HttpResponseRedirect(reverse_lazy('register'))
               
                # validate password
                if(pwd == rpwd):
                    enc_pwd = pbkdf2_sha256.encrypt(
                        pwd, rounds=12000, salt_size=32)
                    create_usr = users(first_name=first_name,
                                       last_name=last_name, email=email, pwd=enc_pwd)
                    create_usr.save()
                    return redirect('login')
                else:
                    # enter error message here
                    messages.error(request, 'Passwords do not match.')
                    return HttpResponseRedirect(reverse_lazy('register'))
           
            except user_token.DoesNotExist:
                messages.error(request, 'No token exists for this user.')
                return HttpResponseRedirect(reverse_lazy('register'))
    else:
        return render(request, 'register.html')

# This function renders the login page and responds to client's POST requests 
def login(request):
    if (request.method == "POST"):
        email = request.POST["email"]
        pwd = request.POST["pwd"]

        #validate user login info
        try:
            obj = users.objects.get(email=email)

            if(pbkdf2_sha256.verify(pwd, obj.pwd)):
                user_data=model_to_dict(obj)
                request.session['user']=user_data
                return redirect('dashboard')
            else:
                messages.error(request, 'Password/email is incorrect.')
                return HttpResponseRedirect(reverse_lazy('login'))
        
        except users.DoesNotExist:
            messages.error(request, 'This email does not have an account.')
            return HttpResponseRedirect(reverse_lazy('login'))
    else:
        return render(request, 'login.html')

# this view renders the share project page and responds to client's POST request
def share(request):
    
    user_data = request.session.get('user')
    email=None
    
    ## NAVBAR rendering
    disp_sb_names = sensor_block.objects.none()
    disp_prj = project.objects.none()
    disp_grp = grp.objects.none()
    x=0
    user_id=user_data['id']

    disp_prj = getDisplayedProjects(user_id)
    selected_project_id=request.session.get('s_p',False)
    selected_group_id=request.session.get('s_g',False)

    if (request.method == "POST"):
        selected_sb_name = request.POST.get('select_blocks',False)
        selected_project_id = request.POST.get('select_project',False)
        selected_group_id = request.POST.get('select_group',False)
        
        print(selected_project_id)

        if(selected_project_id!=False):
            request.session['s_p']=selected_project_id
            request.session['s_g']=False

        else:
            selected_project_id=request.session.get('s_p',False)

        if(selected_group_id!=False):
            request.session['s_g']=selected_group_id
        else:
            selected_group_id=request.session.get('s_g',False)

        if(selected_sb_name!=False):
            request.session['s_sb']=selected_sb_name
        else:
            selected_sb_name=request.session.get('s_sb',False)
    
    disp_grp = getDisplayedGroups(selected_project_id)
    x=disp_grp[0].id
    ## NAVBAR ##

    ## START NOTIFICATIONS ##
    try:
        notifications_all = notification.objects.filter(usr_id=user_data['id']).order_by('-created_at')
    except:
        notifications_all=None
     ## END NOTIFICATIONS ##
    
    ## SHARE LOGIC ##
    if(selected_project_id!=False and selected_group_id!=False and request.method == "POST"):
        email =request.POST.get('email',False)
        access_type_string = request.POST.get("access_type",False)
        access_type = -1

        if(access_type_string == "editor"):
            access_type = 1
        elif(access_type_string == "viewer"):
            access_type = 2

        if(email!=False):
            try:
                obj = users.objects.get(email=email)
                usr_id = obj.id

                share_project = user_access(
                    usr_id=usr_id, project_id=selected_project_id, access_type=access_type)
                share_project.save()
                messages.success(request, 'Your project has been shared with this user.')
                proj=project.objects.get(id=selected_project_id)
                pname = proj.project_name
                msg = "Project "+pname+" has been shared with you by "+user_data['first_name']+" "+user_data['last_name']+"."
                add_notification=notification(usr_id=usr_id,project_id=selected_project_id,msg=msg,created_at=datetime.date.today(),if_read=False)
                add_notification.save()
                return HttpResponseRedirect(reverse_lazy('share'))

                # send email to that user that the project is added to their account
            except users.DoesNotExist:
                token=token_generator()
                create_token = user_token(token=token,invited_email=email, 
                created_at=datetime.date.today(), access_type=access_type, creator_id=user_data['id'])
                create_token.save()
                sendInvitation(receiver_email=email,token=token)
                messages.success(request, 'An invitation has been sent to this user.')
                return HttpResponseRedirect(reverse_lazy('share'))
        else:
            return render(request, 'share-project.html', 
            {'user': user_data,
            'notifications_all': notifications_all,
            'projects':disp_prj,
            'submitted_project_id':int(selected_project_id),
            'groups':disp_grp,
            'x':x,
            'submitted_group_id':int(selected_group_id)})

    else:
        
        return render(request, 'share-project.html', 
        {'user': user_data,
        'notifications_all': notifications_all,
        'projects':disp_prj,
        'submitted_project_id':int(selected_project_id),
        'groups':disp_grp,
        'x':x,
        'submitted_group_id':int(selected_group_id)})


## RENDER DASHBOARD PAGE AND RESPOND TO CLIENT'S POST REQUESTS
def dashboard(request):

    ## INITIALIZE VARIABLES
    single_sensor_data=[]
    Tplot=[]
    SMplot=[]
    Hplot=[]
    phPlot=[]
    chart_sensor_data=[]
    user_data = request.session.get('user')
    disp_sb_names = sensor_block.objects.none()
    disp_prj = project.objects.none()
    disp_grp = grp.objects.none()
    x=0
    user_id=user_data['id']


    disp_prj = getDisplayedProjects(user_id)
    selected_project_id=request.session.get('s_p',False)
    selected_group_id=request.session.get('s_g',False)
    
    growth=False
    health=False
    img_path=False
    
    ## START NOTIFICATIONS ##
    try:
        notifications_all = notification.objects.filter(usr_id=user_id).order_by('-created_at')
    except:
        notifications_all=None
     ## END NOTIFICATIONS ##

    ## START NAVBAR ##
    if(selected_project_id!=False):
        disp_grp = getDisplayedGroups(selected_project_id)
        x=disp_grp[0].id
    if(selected_group_id!=False):
        disp_sb_names = getDisplayedSensorBlocks(selected_group_id)
    
    if (request.method == "POST"):
        selected_sb_name = request.POST.get('select_blocks',False)
        selected_project_id = request.POST.get('select_project',False)
        selected_group_id = request.POST.get('select_group',False)
        
        print(selected_project_id)

        if(selected_project_id!=False):
            request.session['s_p']=selected_project_id
            request.session['s_g']=False

        else:
            selected_project_id=request.session.get('s_p',False)

        if(selected_group_id!=False):
            request.session['s_g']=selected_group_id
        else:
            selected_group_id=request.session.get('s_g',False)

        if(selected_sb_name!=False):
            request.session['s_sb']=selected_sb_name
        else:
            selected_sb_name=request.session.get('s_sb',False)

        print(selected_project_id)
        print("$$$$$$$")
        print(selected_group_id)
        if(selected_group_id!=False):
            print(selected_group_id)
            print(selected_sb_name)
            try:
                if(selected_sb_name!=False):
                    single_sensor_data = getSensorReadings(selected_group_id,selected_sb_name)
                else:
                    selected_sb_name='Average'
            
                if(selected_sb_name=='Average'):
                    chart_sensor_data=getAvgChartData(selected_group_id)
                else:
                    chart_sensor_data=getChartData(selected_group_id,selected_sb_name)
                print(chart_sensor_data)
                n=1
                Tplot,SMplot,Hplot,phPlot = getPlots(chart_sensor_data,n)

            except:
                print('no sensor blocks assigned to group, no data')
            
            disp_sb_names = getDisplayedSensorBlocks(selected_group_id)
        ## END NAVBAR ##
        
        ## LOAD PREDICTIONS AND IMAGES
        disp_grp = getDisplayedGroups(selected_project_id)
        x=disp_grp[0].id
        growth,health,img_path=getPrediction(selected_group_id)
       
        return render(request,'home.html',
        {'user': user_data,
        'sensor_data':single_sensor_data,
        'temp_plot':Tplot,
        'sm_plot':SMplot,
        'ph_plot':phPlot,
        'hum_plot':Hplot,
        'sensor_blocks':disp_sb_names,
        'submitted_sb_name':selected_sb_name,
        'projects':disp_prj,
        'submitted_project_id':int(selected_project_id),
        'groups':disp_grp,
        'x':x,
        'submitted_group_id':int(selected_group_id),
        'notifications_all': notifications_all,
        'growth':growth,
        'health':health,
        'img_path':img_path})
   
    else:
        print("******")
        print(selected_project_id)
        return render(request,'home.html',
        {'user': user_data,
        'sensor_blocks':disp_sb_names,
        'projects':disp_prj,
        'submitted_project_id':int(selected_project_id),
        'groups':disp_grp,
        'x':x,
        'submitted_group_id':int(selected_group_id),
        'notifications_all': notifications_all,
        'growth':growth,
        'health':health,
        'img_path':img_path})
   

# this section is in charge of the newproject page, that generates a newproject
def newproject(request):
    currUser = request.session.get('user')
    userID = currUser['id']
    request.session['group_index'] = 0
    request.session['extra_index'] = 0
    request.session['whichGroup'] = []
    request.session['createdGroups_sID'] = []

    # if the user pressed the submit button, we begin saving the entered details to be saved  into the DB
    if(request.method == "POST"):
        project_name = request.POST["project_name"]
        start_date = request.POST["start_date"]
        end_date = request.POST["end_date"]
        groups_num = request.POST["groups_num"]

        # verify correct date
        if(end_date < start_date):
            messages.error(request, 'Cannot enter end date before start date')
            return HttpResponseRedirect(reverse_lazy('newproject'))

        # if verified details, then create the project, and create an entry in the usr_access table
        # highlighting that this user is a creator (access_type = 0)
        else:
            create_project = project(
                project_name=project_name, start_date=start_date, end_date=end_date)
            create_project.save()
            project_id = create_project.id

            create_usr_access = user_access(usr_id=userID, project_id=project_id, access_type=0)
            create_usr_access.save()

        return redirect(reverse("newgroup", kwargs={'project_id': str(project_id), 'groups_num': str(groups_num)}))

    else:
        return render(request, 'newproject.html',{'user': currUser,})



# this is the function responsible for dealing with the newgroup page.
def newgroup(request, project_id, groups_num):


    # --- Start of Project Selection Dropdown Options --- #

    # retrieve user ID to later get all settings related to this user
    user_data = request.session.get('user')
    userID = user_data['id']

    userSettings = []
    settingsNames = []
    settingsIDs = []

    # get all projects relating to this user
    userProjects = user_access.objects.filter(usr_id = userID).only('project_id')
 
    # checks if the user has any settings
    try:
        settingsCounter = 0

        # get all groups relating to this user's projects
        for proj in userProjects:
            projID = proj.project_id
            query = grp.objects.filter(project_id = projID)
            for i in range (len(query)):
                currQuery = query[i].settings_id

                # to remove any duplicates
                noAdd = True
                for checkDups in userSettings:
                    if checkDups == currQuery:
                        noAdd = False

                if noAdd:
                    userSettings.append(currQuery)

        # get all settings from all groups relating to this user's projects
        namesCounter = 0    
        for setts in userSettings:
            query = settings.objects.filter(id = setts)
 
            for i in range (len(query)):
                currQueryName = query[i].name
                settingsNames.append(currQueryName)
                currQueryID = query[i].id
                settingsIDs.append(currQueryID)
                namesCounter = namesCounter + 1      
 
 
    except grp.DoesNotExist: 
        userSettings = None
        settingsNames = None  
        settingsIDs = None  
        settingsInfo = None
 
    settingsInfo = list(zip(settingsNames, settingsIDs))

    # --- End of Project Selection Dropdown Options --- #

    group_ids = []
    num_sensors = []

    project_obj = project.objects.get(id=project_id)
    project_name = project_obj.project_name

    # a model formset to generate the form based on the # of groups variable entered by the
    # user in the previous page (newproject)
    SettingsFormSet = modelformset_factory(settings, exclude=(), extra = int(groups_num))
    form_set = SettingsFormSet(queryset=settings.objects.none())

    # entering information into DB if the submit button was pressed.    
    # checks if the form is valid and if any dropdown settings were selected thoughout.
    # proceeds then to generate the sensorblocks page based on the # of sensorblocks the user entered for the group.
    if request.method == "POST" and 'group_btn' in request.POST:
        form_set = SettingsFormSet(request.POST or None, request.FILES or None)
        camera_ids = request.POST.getlist('camera_id')
        x = 0
        for form in form_set:
            if form_set.is_valid:
                val = form.save(commit=False)
                sID_Dropdown_List = request.session.get('createdGroups_sID')
                
                # checks if fields were left empty. Ideally we check them all.
                # adds the entered details from the form to be saved into the group in the DB.
                if val.name != '' or val.max_ph != None:
                    val.save()
                    sId = int(val.id)

                    camera_id = camera_ids[x]
                    x = x + 1

                    create_grp = grp(project_id = int(project_id), settings_id = sId, camera_id = camera_id)
                    create_grp.save()
                    group_ids.append(int(create_grp.id))

                    number_of_sensor_blocks = form.cleaned_data['number_of_sensor_blocks']
                    num_sensors.append(int(number_of_sensor_blocks))

                # so user selected from dropdown, so we'll retrieve the settingsID from the session
                # to be saved into the group in the DB
                elif len(sID_Dropdown_List) > 0:     
                    sId = sID_Dropdown_List[0]
                    sID_Dropdown_List.pop(0)
                    request.session['createdGroups_sID'] = sID_Dropdown_List

                    camera_id = camera_ids[x]
                    x = x + 1

                    create_grp = grp(project_id = int(project_id), settings_id = sId, camera_id = camera_id)                   
                    create_grp.save()
                    group_ids.append(int(create_grp.id))

                    currSettingsObject = settings.objects.get(id = sId)
                    number_of_sensor_blocks = currSettingsObject.number_of_sensor_blocks
                    num_sensors.append(int(number_of_sensor_blocks))

        # for the sensorblock form
        request.session['group_ids'] = group_ids
        request.session['num_sensors'] = num_sensors
        request.session['first'] = True

        # First sensor form
        SensorFormSet = modelformset_factory(sensor_block, exclude=('group_id','sensor_block_name',), extra = num_sensors[0])
        sensor_set = SensorFormSet(queryset = sensor_block.objects.none())
        return render(request, 'sensors.html',{'sensor_set':sensor_set, 'group':1,'user': user_data})
    
    if request.method != "POST":
        return render(request, 'newgroup.html',{'project_name':project_name, 'form_set':form_set,'user': user_data, 
        'namesCounter':range(namesCounter), 'settingsInfo':settingsInfo})

    # Rest of sensor forms
    num_sensors = request.session.get('num_sensors')
    group_ids = request.session.get('group_ids')
    SensorFormSet = modelformset_factory(sensor_block, exclude=('group_id','sensor_block_name',), extra = num_sensors[0])
    sensor_set = SensorFormSet(queryset = sensor_block.objects.none())

    # saving the sensorblock form details into the sensorblock entity into the DB.
    if request.method == "POST" and 'sensor_btn' in request.POST:
        sensor_set = SensorFormSet(request.POST or None, request.FILES or None)
        page_num = request.session.get('page_num')
        sensor_names = request.POST.getlist('sensor_block_name')
        group_index = request.session.get('group_index')
        sensor_index = 0

        for sensor in sensor_set:
            create_sensor = sensor_block(group_id = group_ids[group_index], sensor_block_name = sensor_names[sensor_index]).save()
            sensor_index = sensor_index + 1
        request.session['group_index'] = request.session.get('group_index') + 1

    request.session['extra_index'] = request.session.get('extra_index') + 1
    extra_index = request.session.get('extra_index')
    length = len(num_sensors)
    if extra_index == len(num_sensors):
        return redirect('/app/')
    else:
        SensorFormSet = modelformset_factory(sensor_block, exclude=('group_id','sensor_block_name',), extra = num_sensors[extra_index])
        sensor_set = SensorFormSet(queryset = sensor_block.objects.none())
        return render(request, 'sensors.html',{'sensor_set':sensor_set,'group':extra_index+1,'user': user_data})

def update_settings_dropdown(request, project_id, groups_num):
    dropdownValue = request.GET.get('dropdownValue')

    # gets the settingsID from the dropdown selected, then saves it in the session to be later saved into the
    # DB using the newgroup function, as explained there.
    if dropdownValue != 0: 
        currG_sID = request.session.get('createdGroups_sID')
        currG_sID.append(dropdownValue)
        request.session['createdGroups_sID'] = currG_sID
    return render(request, 'EmptyPage.html')


def project_settings(request):

    user_data = request.session.get('user')

    # retrieve notifications
    try:
        notifications_all = notification.objects.filter(usr_id=user_data['id']).order_by('-created_at')
    except:
        notifications_all=None

     ## NAVBAR

    disp_sb_names = sensor_block.objects.none()
    disp_prj = project.objects.none()
    disp_grp = grp.objects.none()
    x=0
    user_id=user_data['id']

    # retrieves the user's projects, along with their variables, to be edited
    disp_prj = getDisplayedProjects(user_id)
    selected_project_id=request.session.get('s_p',False)
    selected_group_id=request.session.get('s_g',False)

    # update the project settings based on entered variables
    # checks if entered variables are valid thoughout.
    if (request.method == "POST"):
        selected_project_id = request.POST.get('select_project',False)
        selected_group_id = request.POST.get('select_group',False)
        
        print(selected_project_id)

        if(selected_project_id!=False):
            request.session['s_p']=selected_project_id
            request.session['s_g']=False

        else:
            selected_project_id=request.session.get('s_p',False)

        if(selected_group_id!=False):
            request.session['s_g']=selected_group_id
        else:
            selected_group_id=request.session.get('s_g',False)

    ## NAVBAR

    project_obj = project.objects.get(id = selected_project_id)
    project_name = project_obj.project_name

    ProjectSettings = modelformset_factory(model=project,form = projectForm, exclude = (), extra = 0)
    form_set = ProjectSettings(queryset=project.objects.filter(id=selected_project_id))
    
    if request.method == "POST":
        form_set = ProjectSettings(request.POST or None, request.FILES or None)
        if form_set.is_valid:
            form_set.save()
            return redirect('/app/')

    return render(request, 
    'project_settings.html',
    {'project_name':project_name, 
    'form_set':form_set,
    'user': user_data,
    'projects':disp_prj,
    'submitted_project_id':int(selected_project_id),
    'groups':disp_grp,
    'x':x,
    'submitted_group_id':int(selected_group_id), 
    'notifications_all': notifications_all})


# same logic as the project_settings 
def group_settings(request):

    user_data = request.session.get('user')
    try:
        notifications_all = notification.objects.filter(usr_id=user_data['id']).order_by('-created_at')
    except:
        notifications_all=None

     ## NAVBAR

    disp_sb_names = sensor_block.objects.none()
    disp_prj = project.objects.none()
    disp_grp = grp.objects.none()
    x=0
    user_id=user_data['id']

    disp_prj = getDisplayedProjects(user_id)
    selected_project_id=request.session.get('s_p',False)
    selected_group_id=request.session.get('s_g',False)

    if (request.method == "POST"):
        selected_project_id = request.POST.get('select_project',False)
        selected_group_id = request.POST.get('select_group',False)
        
        print(selected_project_id)

        if(selected_project_id!=False):
            request.session['s_p']=selected_project_id
            request.session['s_g']=False

        else:
            selected_project_id=request.session.get('s_p',False)

        if(selected_group_id!=False):
            request.session['s_g']=selected_group_id
        else:
            selected_group_id=request.session.get('s_g',False)

    ## NAVBAR
    
    grp_obj = grp.objects.get(id = selected_group_id)
    project_name = project.objects.get(id = selected_project_id).project_name
    settings_id = grp_obj.settings_id

    GroupSettings = modelformset_factory(settings, exclude = (), extra = 0)
    form_set = GroupSettings(queryset=settings.objects.filter(id=settings_id))
    
    if request.method == "POST":
        form_set = GroupSettings(request.POST or None, request.FILES or None)
        if form_set.is_valid:
            form_set.save()
            return redirect('/app/')

    return render(request, 
    'group_settings.html',
    {'project_name':project_name, 
    'group_name':str(int(selected_group_id)-230+1), 
    'form_set':form_set,
    'user': user_data,
    'projects':disp_prj,
    'submitted_project_id':int(selected_project_id),
    'groups':disp_grp,
    'x':x,
    'submitted_group_id':int(selected_group_id),
    'notifications_all': notifications_all})

# this is in charge of changing the password.
def change_password(request):
    currUser = request.session.get('user')
    user_id = currUser['id']

    # by getting the userID from the session, we can retrieve their current password and their email
    user_password = users.objects.get(id = user_id).pwd
    user_email = users.objects.get(id = user_id).email
    print(user_email)

    if (request.method == "POST"):
        old_password = request.POST["old_password"]
        new_password = request.POST["new_password"]
        repeat_password = request.POST["repeat_password"]

        # if the password they entered as verification is the same as the user's actual password...
        if(pbkdf2_sha256.verify(old_password, user_password)):
            # check also if th repeat password field has the same password as the new password field
            # if so, then update the password.
            if(new_password == repeat_password):
                enc_pwd = pbkdf2_sha256.encrypt(new_password, rounds=12000, salt_size=32)
                users.objects.filter(id = user_id).update(pwd = enc_pwd)
                return redirect('/app/')
            else:
                messages.error(request, 'Password and repeat password are different')
        else:
            messages.error(request, 'Old password is incorrect')
        
    return render(request, 'change_password.html')