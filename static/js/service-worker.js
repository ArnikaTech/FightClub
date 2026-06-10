const CACHE_NAME = 'stars-v1';
const urlsToCache = [
    '/',
    '/static/css/app.css',
    '/static/js/app.js',
    '/static/vendors/bootstrap/bootstrap.rtl.min.css',
    '/static/vendors/bootstrap-icons/bootstrap-icons.css',
];

self.addEventListener('install', function(event) {
    event.waitUntil(
        caches.open(CACHE_NAME).then(function(cache) {
            return cache.addAll(urlsToCache);
        })
    );
});

self.addEventListener('fetch', function(event) {
    event.respondWith(
        caches.match(event.request).then(function(response) {
            return response || fetch(event.request);
        })
    );
});