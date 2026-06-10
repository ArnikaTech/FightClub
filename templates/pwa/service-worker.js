{% load static %}
const APP_VERSION = 'stars-pwa-{{ sw_version }}';
const STATIC_CACHE = `${APP_VERSION}-static`;
const PAGE_CACHE = `${APP_VERSION}-pages`;
const OFFLINE_URL = '/';

const STATIC_ASSETS = [
    OFFLINE_URL,
    "{% static 'css/app.css' %}",
    "{% static 'css/fonts.css' %}",
    "{% static 'js/app.js' %}",
    "{% static 'vendors/bootstrap/bootstrap.rtl.min.css' %}",
    "{% static 'vendors/bootstrap/bootstrap.bundle.min.js' %}",
    "{% static 'vendors/bootstrap-icons/bootstrap-icons.css' %}",
    "{% static 'vendors/bootstrap-icons/fonts/bootstrap-icons.woff2' %}",
    "{% static 'vendors/jquery/jquery.min.js' %}",
    "{% static 'vendors/htmx/htmx.min.js' %}",
    "{% static 'vendors/select2/select2.min.css' %}",
    "{% static 'vendors/select2/select2.min.js' %}",
    "{% static 'vendors/animate/animate.min.css' %}",
    "{% static 'fonts/Vazirmatn/Vazirmatn-RD-FD-Regular.woff2' %}",
    "{% static 'fonts/Vazirmatn/Vazirmatn-RD-FD-Bold.woff2' %}",
    "{% static 'pwa/icons/icon-192x192.png' %}",
    "{% static 'pwa/icons/icon-512x512.png' %}",
    "{% url 'manifest' %}",
];

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(STATIC_CACHE)
            .then((cache) => cache.addAll(STATIC_ASSETS))
            .then(() => self.skipWaiting())
    );
});

self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys()
            .then((keys) => Promise.all(
                keys
                    .filter((key) => !key.startsWith(APP_VERSION))
                    .map((key) => caches.delete(key))
            ))
            .then(() => self.clients.claim())
    );
});

self.addEventListener('message', (event) => {
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
});

self.addEventListener('fetch', (event) => {
    const request = event.request;
    const url = new URL(request.url);

    if (request.method !== 'GET' || url.origin !== self.location.origin) {
        return;
    }

    if (request.mode === 'navigate') {
        event.respondWith(networkFirstPage(request));
        return;
    }

    if (isStaticAsset(request)) {
        event.respondWith(cacheFirst(request, STATIC_CACHE));
        return;
    }

    event.respondWith(staleWhileRevalidate(request, PAGE_CACHE));
});

function isStaticAsset(request) {
    const { pathname } = new URL(request.url);
    return pathname.startsWith('/static/') || pathname === '/manifest.json';
}

async function cacheFirst(request, cacheName) {
    const cached = await caches.match(request);
    if (cached) return cached;

    const response = await fetch(request);
    if (response && response.ok) {
        const cache = await caches.open(cacheName);
        cache.put(request, response.clone());
    }
    return response;
}

async function networkFirstPage(request) {
    const cache = await caches.open(PAGE_CACHE);
    try {
        const response = await fetch(request);
        if (response && response.ok) {
            cache.put(request, response.clone());
        }
        return response;
    } catch (error) {
        return (await cache.match(request)) || (await caches.match(OFFLINE_URL));
    }
}

async function staleWhileRevalidate(request, cacheName) {
    const cache = await caches.open(cacheName);
    const cached = await cache.match(request);
    const networkFetch = fetch(request)
        .then((response) => {
            if (response && response.ok) {
                cache.put(request, response.clone());
            }
            return response;
        })
        .catch(() => cached);

    return cached || networkFetch;
}
