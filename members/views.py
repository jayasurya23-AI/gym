from django.http import request
from django.http.response import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.views.generic import TemplateView, CreateView, UpdateView, DetailView, DeleteView, ListView
from .models import Member
from django.contrib.auth.decorators import login_required
from .forms import AddMemberForm, AddMemberUpdateForm
from django.contrib.auth.mixins import LoginRequiredMixin
import dateutil.relativedelta as delta
from django.urls import reverse
from wallpaper.models import Wallpaper
from payments.models import Payments
from reports.views import export_all


class LandingPage(TemplateView):
    template_name = "landing_page.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        if Wallpaper.objects.filter()[:1].exists():
            wallpaper = Wallpaper.objects.filter()[:1].get()
            context.update({
                'wallpaper': wallpaper
            })

        return context


def view_members(request):
    data = Member.objects.filter(stop=0).order_by('first_name')
    return render(request, "members/view_members.html", {
        'data': data
    })


class MemberListView(LoginRequiredMixin, ListView):
    template_name = 'members/view_members.html'
    context_object_name = 'data'

    def get_queryset(self):
        members = Member.objects.filter(stop=0).order_by('first_name')
        return members

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        stopped_members = Member.objects.filter(stop=1).order_by('first_name')
        if stopped_members.exists():
            print('yes')
            context.update({
                'stopped_member_data': stopped_members
            })
        return context


class AddMemberView(LoginRequiredMixin, CreateView):
    template_name = 'members/add_member.html'
    form_class = AddMemberForm

    def get_success_url(self) -> str:
        return reverse("members:member-list")

    def form_valid(self, form):
        form.instance.registration_upto = form.cleaned_data['registration_date'] + delta.relativedelta(
            months=int(form.cleaned_data['subscription_period']))
        self.object = form.save()

        if form.cleaned_data['fee_status'] == 'paid':
            payments = Payments(
                user=self.object,
                payment_date=form.cleaned_data['registration_date'],
                payment_period=form.cleaned_data['subscription_period'],
                payment_amount=form.cleaned_data['amount'])
            payments.save()
        return HttpResponseRedirect(self.get_success_url())


class MemberDetailView(LoginRequiredMixin, DetailView):
    template_name = 'members/member_detail.html'
    context_object_name = 'member'
    queryset = Member.objects.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        payments = Payments.objects.filter(user=self.kwargs['pk'])
        if not payments.exists():
            payments = 'No Records'
        context.update({
            'member_payment': payments
        })
        return context


class UpdateMemberView(LoginRequiredMixin, UpdateView):
    template_name = 'members/update_member.html'
    form_class = AddMemberUpdateForm
    queryset = Member.objects.all()

    def get_success_url(self) -> str:
        return reverse("members:member-list")

    def form_valid(self, form):
        form.instance.registration_upto = form.cleaned_data['registration_date'] + delta.relativedelta(
            months=int(form.cleaned_data['subscription_period']))
        self.object = form.save()

        if form.cleaned_data['fee_status'] == 'paid':
            check = Payments.objects.filter(
                payment_date=form.cleaned_data['registration_date'], user=self.object).count()
            if check == 0:
                payments = Payments(
                    user=self.object,
                    payment_date=form.cleaned_data['registration_date'],
                    payment_period=form.cleaned_data['subscription_period'],
                    payment_amount=form.cleaned_data['amount'])
                payments.save()

        return HttpResponseRedirect(self.get_success_url())


class DeleteMemberView(LoginRequiredMixin, DeleteView):
    template_name = 'members/member_delete.html'
    queryset = Member.objects.all()

    def get_success_url(self) -> str:
        return reverse("members:member-list")
