from urllib.parse import urlencode

from django.shortcuts import redirect
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin

from .models import Organization


class ActiveOrganizationMiddleware(MiddlewareMixin):
    """Persist the platform owner's organization filter across control-panel pages."""

    SESSION_KEY = 'active_organization_id'
    QUERY_KEY = 'organization_id'

    def process_request(self, request):
        user = request.user
        if not user.is_authenticated or not user.is_super_manager:
            request.active_organization_id = None
            return None

        if self.QUERY_KEY in request.GET:
            raw_id = request.GET.get(self.QUERY_KEY, '').strip()
            if not raw_id:
                request.session.pop(self.SESSION_KEY, None)
            else:
                try:
                    org_id = int(raw_id)
                except (TypeError, ValueError):
                    org_id = None
                if org_id and Organization.objects.filter(pk=org_id, is_active=True).exists():
                    request.session[self.SESSION_KEY] = org_id
                else:
                    request.session.pop(self.SESSION_KEY, None)

            query = request.GET.copy()
            query.pop(self.QUERY_KEY, None)
            target = request.path
            if query:
                target = f'{target}?{urlencode(query, doseq=True)}'
            return redirect(target)

        org_id = request.session.get(self.SESSION_KEY)
        if org_id and not Organization.objects.filter(pk=org_id, is_active=True).exists():
            request.session.pop(self.SESSION_KEY, None)
            org_id = None
        request.active_organization_id = org_id
        user.active_organization_id = org_id
        return None
