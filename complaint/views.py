# -*- coding: utf-8 -*-

from django.shortcuts import render, HttpResponseRedirect
from models import Complaint, Status
from forms import NewComplaint
from datetime import datetime, timedelta



def home(request, complaint_type=None):
    today = datetime.utcnow()
    control_date = timedelta(days=27)
    TYPES = {'consultation': 1, 'complain': 2, 'expertise': 3}
    if complaint_type in TYPES:
        complaints = Complaint.objects.filter(kind=TYPES.get(complaint_type))[:30]
    else:
        complaints = Complaint.objects.all()[:30]

    return render(request, 'complaint/index.html',
                  {'complaint_type': complaint_type,
                   'complaints': complaints,
                   'today': today.date(),
                   'control_date': today.date()-control_date})


def new(request):
    form = NewComplaint()

    if request.method == 'POST':
        new_complaint = NewComplaint(request.POST)
        if new_complaint.is_valid():
            complaint = new_complaint.save()
            status = Status(complaint=complaint, date=datetime.utcnow(), type=1)
            status.save()
            return HttpResponseRedirect('/complaint/')

    return render(request, 'complaint/new.html',
                  {'form': form})


def edit(request, complaint_id=None):
    if complaint_id:
        complaint = Complaint.objects.get(pk=complaint_id)
    else:
        complaint = None

    form = NewComplaint(instance=complaint)
    if request.method == 'POST':
        edit_complaint = NewComplaint(request.POST, instance=complaint)
        edit_complaint.save()
        return HttpResponseRedirect('/complaint/')

    return render(request, 'complaint/edit.html',
                  {'form': form, 'complaint': complaint})