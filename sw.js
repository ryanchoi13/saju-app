// 이전 캐시 강제 무효화 및 네트워크 우선 연결
self.addEventListener('install', (event) => {
    self.skipWaiting();
});

self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys().then((keys) => {
            return Promise.all(keys.map((key) => caches.delete(key)));
        }).then(() => self.clients.claim())
    );
});

self.addEventListener('fetch', (event) => {
    // 캐시 없이 항상 최신 서버 파일 호출
    event.respondWith(fetch(event.request));
});
