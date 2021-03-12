from django.db.models import Func, F, Q
from django.shortcuts import get_object_or_404
from rest_framework import serializers

from apps.core import models
from apps.news.models import RawNews, Company, LawFirm
from apps.news.serializers import AddRawNewsSerializer
from apps.core.models import Opportunity, News, NewsPackage, Package
from apps.accounts.models import ClientAdmin
import math

# SERIALIZING DATA IN DJANGO REST FRAMEWORK IS VERY NECESSARY.
# EXAMPLES OF SIMPLE/COMPLEX SERIALIZERS I CREATED AND MAINTAINED


class PackageIndustriesSerializer(serializers.ModelSerializer):
    industry_id = serializers.SerializerMethodField()
    industry_name = serializers.SerializerMethodField()

    class Meta:
        model = models.Package
        fields = ('industry_id', 'industry_name')

    def get_industry_id(self, instance):
        return instance.industry.id

    def get_industry_name(self, instance):
        return instance.industry.name


class NewCompanyInformationsSerializer(serializers.ModelSerializer):
    lawfirm_Used = LawFirmSerializer(read_only=True, many=True)
    company_news = serializers.SerializerMethodField()
    key_employees = serializers.SerializerMethodField()
    vertical_sector_name = serializers.SerializerMethodField()
    peer_companies = serializers.SerializerMethodField()
    marketcap = serializers.SerializerMethodField()
    revenue_mil = serializers.SerializerMethodField()
    package = serializers.SerializerMethodField()
    funding_amount_mil = serializers.SerializerMethodField()

    class Meta:
        model = models.Company
        fields = ('id', 'name', 'logo_url', 'description', 'dt_updated',
                  'source', 'vertical_sector_name', 'company_type',
                  'marketcap', 'revenue_mil', 'funding_amount_mil',
                  'funding_date', 'company_news', 'key_employees',
                  'lawfirm_Used', 'peer_companies', 'package')

    def get_package(self, instance):
        request = self.context.get('request')
        if request:
            if hasattr(request.user, 'enduser'):
                user_packages = request.user.enduser.packages.all()
            elif request.user.is_staff:
                user_packages = Package.objects.all()
            else:
                raise AttributeError()

        for each_package in user_packages:
            each_package_company_list = [company.pk for company in
                                         each_package.companies.all()]
            if instance.id in each_package_company_list:
                return each_package.id

    def millify_mil(self, n):
        n = float(n)
        if n > 1000000000:
            return '{}{:.2f}{}'.format('$', (n / 1000000000), 'B')
        else:
            return '{}{:.2f}{}'.format('$', (n / 1000000), 'M')

    def get_funding_amount_mil(self, instance):
        if (instance.funding_amount == 0 or instance.funding_amount is None):
            return 0
        else:
            return self.millify_mil(instance.funding_amount)

    def get_revenue_mil(self, instance):
        if (instance.revenue == 0 or instance.revenue is None):
            return 0
        else:
            return self.millify_mil(instance.revenue)

    def get_marketcap(self, instance):
        if (instance.market_cap == 0 or instance.market_cap is None):
            return 'N/A'
        else:
            return self.millify_mil(instance.market_cap)

    def get_vertical_sector_name(self, instance):
        ''' return vertical also once vetical created on company model'''
        if instance.sector:
            return instance.sector.name

    def get_key_employees(self, instance):
        key_employees = instance.peoples.all().order_by('id').values(
            'id', 'name', 'position', 'linkedin')
        return key_employees

    def get_categories(self, news):
        return news.subcategory.values('name')

    def get_company_news(self, instance):
        news = News.objects.filter(~Q(content_type='{}'),
                                   news__company=instance)\
            .order_by('-news__date')
        company_news = [
            {'id': each_news.id,
             'title': each_news.title,
             'news_url': each_news.news.source,
             'title_link': f'<a href="{each_news.news.source}" \
                target="_blank">{each_news.title}</a>',
             'company': instance.name,
             'company_logo': instance.logo_url,
             'date': each_news.news.date,
             'snippet': each_news.snippet,
             'subcategories': self.get_categories(each_news),
             'opportunities': each_news.opportunities.values('sentence'),
             }
            for each_news in news
            if each_news.content_type.get('company_page') == 1
        ]
        return company_news

    def get_peer_companies(self, instance):
        if instance.peer_companies.exists():
            return instance.peer_companies.all().values(
                'id', 'name', 'logo', 'description')
        else:
            if instance.company_type == 'Public':
                peers = Company.objects.filter(
                    sector=instance.sector,
                    company_type=instance.company_type,
                )\
                    .exclude(pk=instance.pk)\
                    .annotate(abs_diff=Func(F('market_cap') - instance.market_cap, function='ABS')).order_by('abs_diff')\
                    .values('id', 'name', 'logo', 'market_cap', 'description')[:3]
            else:
                peers = Company.objects.filter(sector=instance.sector, company_type=instance.company_type)\
                        .exclude(pk=instance.pk) \
                        .annotate(abs_diff=Func(F('funding_amount') - instance.funding_amount, function='ABS')).order_by('abs_diff') \
                        .values('id', 'name', 'logo', 'description')[:3]
            return peers