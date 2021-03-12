# AN EXAMPLE OF TESTS WRITTEN FOR THE VIEW ENDPOINTS ON THE REST API

from django.utils import timezone
from django.urls import reverse
from rest_framework import status

from apps.accounts.models import User
from apps.front.tests import TestCaseHelper
from apps.news.models import Industry, CompanyGroup, Company, RawNews, \
    SubCategory, Category, Sector, Vertical
from apps.news.tasks import delete_old_discarded_news, \
    delete_one_year_old_raw_news


class TestNewsViews(TestCaseHelper):
    """ test apps.news.views """

    def setUp(self):
        self.sector = Sector.objects.create(name='test')
        self.industry = Industry.objects.create(name='test')
        Industry.objects.get(name="test").sector.add(self.sector)
        self.vertical = Vertical.objects.create(name='test')
        self.group = CompanyGroup.objects.create(name='test')
        self.cat = SubCategory.objects.create(
            name='test', category=Category.objects.create(name='test'))
        self.company = Company.objects.create(
            company_id='test',
            name='test',
            description='test',
            source='test',
            sector=self.sector,
            vertical=self.vertical,
            company_type='test',
            exchange='test',
            extra={'test': 'test'},
            group=self.group,
        )
        self.company.industries.add(self.industry)
        User.objects.get(
            email='test@analyst.com').analyst.company_groups.add(self.group)
        self.raw_news = RawNews.objects.create(
            company=self.company,
            title='test',
            snippet='test',
            content='test',
            source='test',
            date=timezone.now(),
        )

        self.raw_news.subcategory.add(self.cat)
        super().setUp()

    def test_raw_news_list_new(self):
        logged = self.login('test@analyst.com')
        self.assertTrue(logged)

        response = self.client.get(reverse('raw_news_new', kwargs={
            'pk': self.group.pk,
        }))
        self.assertTrue(response.status_code == status.HTTP_200_OK)
        self.assertTrue(
            response.data['results']['data'][0]['id'] == self.raw_news.id,
            response.data)

    def test_search_raw_news(self):
        logged = self.login('test@analyst.com')
        self.assertTrue(logged)

        response = self.client.get(reverse('search_raw_news'))

        self.assertTrue(response.status_code == status.HTTP_200_OK)

    def test_rawnews_verticals_group(self):
        logged = self.login('test@analyst.com')
        self.assertTrue(logged)

        response = self.client.get(reverse('rawnews_verticals_group', kwargs={
            'pk': self.group.pk,
        }))

        self.assertTrue(response.status_code == status.HTTP_200_OK)
        self.assertTrue(
            response.data['verticals'][0]['value'] == self.vertical.id
        )

    def test_all_analyst_verticals(self):
        logged = self.login('test@analyst.com')
        self.assertTrue(logged)

        response = self.client.get(reverse('all_analyst_verticals'))

        self.assertTrue(response.status_code == status.HTTP_200_OK)
        self.assertTrue(
            response.data['verticals'][0]['value'] == self.vertical.id
        )

    def test_all_analyst_industries(self):
        logged = self.login('test@analyst.com')
        self.assertTrue(logged)

        response = self.client.get(reverse('all_analyst_industries'))

        self.assertTrue(response.status_code == status.HTTP_200_OK)
        self.assertTrue(
            response.data['industries'][0]['value'] == self.industry.id
        )

    def test_rawnews_industries_group(self):
        logged = self.login('test@analyst.com')
        self.assertTrue(logged)

        response = self.client.get(reverse('rawnews_industries_group', kwargs={
            'pk': self.group.pk,
        }))

        self.assertTrue(response.status_code == status.HTTP_200_OK)
        self.assertTrue(
            response.data['industries'][0]['value'] == self.industry.id
        )

    def test_rawnews_sectors(self):
        logged = self.login('test@analyst.com')
        self.assertTrue(logged)

        response = self.client.get(reverse('rawnews_sectors', kwargs={
            'industry_pk': self.industry.pk,
        }))

        self.assertTrue(response.status_code == status.HTTP_200_OK)
        self.assertTrue(
            response.data['sectors'][0]['value'] == self.sector.id
        )

    def test_all_analyst_companies(self):
        logged = self.login('test@analyst.com')
        self.assertTrue(logged)

        response = self.client.get(reverse('all_analyst_companies', kwargs={
            'group_pk': self.group.pk,
            'sector_pk': self.sector.pk
        }))

        self.assertTrue(response.status_code == status.HTTP_200_OK)
        self.assertTrue(
            response.data['companies'][0]['value'] == self.company.id
        )

    def test_analyst_group_companies(self):
        logged = self.login('test@analyst.com')
        self.assertTrue(logged)

        response = self.client.get(reverse('analyst_group_companies', kwargs={
            'group_pk': self.group.pk,
        }))

        self.assertTrue(response.status_code == status.HTTP_200_OK)
        self.assertTrue(
            response.data['companies'][0]['value'] == self.company.id
        )

    def test_analyst_vertical_companies(self):
        logged = self.login('test@analyst.com')
        self.assertTrue(logged)

        response = self.client.get(
            reverse('analyst_vertical_companies', kwargs={
                'group_pk': self.group.pk,
                'vertical_pk': self.vertical.pk
            }))

        self.assertTrue(response.status_code == status.HTTP_200_OK)
        self.assertTrue(
            response.data['companies'][0]['value'] == self.company.id
        )

    def test_raw_news_list(self):
        """
        test raw news list endpoint
        Get list of raw news for company group X (if analyst has access)
        """
        logged = self.login('test@analyst.com')
        self.assertTrue(logged)

        response = self.client.get(reverse('raw_news', kwargs={
            'pk': self.group.pk,
        }))

        self.assertTrue(response.status_code == status.HTTP_200_OK)
        # custom serializer have a list `data` in `results`
        self.assertTrue(
            response.data['results']['data'][0]['id'] == self.raw_news.id,
            response.data)

    def test_raw_news_details(self):
        """
        test raw news details endpoint
        Get details and update a single raw news (if analyst has access)
        """
        logged = self.login('test@analyst.com')
        self.assertTrue(logged)

        response = self.client.get(reverse('raw_news_details', kwargs={
            'pk': self.raw_news.pk,
        }))

        self.assertTrue(
            response.status_code == status.HTTP_200_OK, response.data)
        self.assertTrue(response.data['id'] == self.raw_news.id)

    def test_discarded_raw_news(self):
        """
        test discarded raw news endpoint
        List of discarded raw news
        """
        logged = self.login('test@analyst.com')
        self.assertTrue(logged)

        response = self.client.get(reverse('discarded_raw_news'))
        self.assertTrue(response.status_code == status.HTTP_200_OK)
        self.assertTrue(len(response.data['results']) == 0)

        self.raw_news.discarded = True
        self.raw_news.save(update_fields=['discarded'])

        response = self.client.get(reverse('discarded_raw_news'))
        self.assertTrue(response.status_code == status.HTTP_200_OK)
        self.assertTrue(len(response.data['results']) == 1)

    def test_discarded_raw_news_details(self):
        """
        test discarded raw news details
        Get details and update a single discarded raw news
        (if analyst has access)
        """
        logged = self.login('test@analyst.com')
        self.assertTrue(logged)

        response = self.client.get(reverse(
            'discard_raw_news_details', kwargs={'pk': self.raw_news.pk}))
        self.assertTrue(response.status_code == status.HTTP_404_NOT_FOUND)

        self.raw_news.discarded = True
        self.raw_news.save(update_fields=['discarded'])

        response = self.client.get(reverse(
            'discard_raw_news_details', kwargs={'pk': self.raw_news.pk}))
        self.assertTrue(response.status_code == status.HTTP_200_OK)
        self.assertTrue(response.data['id'] == self.raw_news.id)
